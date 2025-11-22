"""
Wav2Lip Inference Module - 모델 재사용을 위한 함수형 인터페이스
"""
import numpy as np
import cv2
import os
import subprocess
import platform
import torch
import face_detection
import audio
from models import Wav2Lip
from tqdm import tqdm
import time

mel_step_size = 16

def increase_frames(frames, target_length):
	"""
	영상 프레임을 오디오 길이에 맞춰 균등하게 확장 (벡터화 최적화)
	프레임을 복제하여 목표 길이까지 늘림 (순환 재생이 아닌 연속 확장)
	
	Args:
		frames: 원본 프레임 리스트
		target_length: 목표 프레임 수
		
	Returns:
		확장된 프레임 리스트
	"""
	if len(frames) >= target_length:
		return frames[:target_length]
	
	# 벡터화된 확장: 각 프레임의 반복 횟수를 미리 계산
	original_len = len(frames)
	ratio = target_length / original_len
	
	# 각 프레임이 몇 번 반복되어야 하는지 계산
	repeat_counts = np.ones(original_len, dtype=int)
	remaining = target_length - original_len
	
	# 균등하게 분배
	if remaining > 0:
		dup_every = original_len / remaining
		next_dup = 0.0
		added = 0
		
		while added < remaining and next_dup < original_len:
			idx = int(next_dup)
			if idx < original_len:
				repeat_counts[idx] += 1
				added += 1
			next_dup += dup_every
	
	# NumPy 배열로 변환하여 벡터화된 확장 수행
	frames_array = np.array(frames)
	expanded_frames = []
	
	for i, count in enumerate(repeat_counts):
		for _ in range(count):
			expanded_frames.append(frames[i])
	
	return expanded_frames[:target_length]

def expand_face_det_results(face_det_results, target_length):
	"""
	얼굴 감지 결과를 목표 길이로 확장
	프레임 확장과 동일한 비율로 얼굴 감지 결과도 확장
	
	Args:
		face_det_results: 원본 얼굴 감지 결과 리스트
		target_length: 목표 길이
		
	Returns:
		확장된 얼굴 감지 결과 리스트
	"""
	if len(face_det_results) >= target_length:
		return face_det_results[:target_length]
	
	original_len = len(face_det_results)
	ratio = target_length / original_len
	
	# 각 결과의 반복 횟수 계산
	repeat_counts = np.ones(original_len, dtype=int)
	remaining = target_length - original_len
	
	if remaining > 0:
		dup_every = original_len / remaining
		next_dup = 0.0
		added = 0
		
		while added < remaining and next_dup < original_len:
			idx = int(next_dup)
			if idx < original_len:
				repeat_counts[idx] += 1
				added += 1
			next_dup += dup_every
	
	# 얼굴 감지 결과 확장 (이미지 복사보다 훨씬 빠름)
	expanded_results = []
	for i, count in enumerate(repeat_counts):
		for _ in range(count):
			# 얼굴 영역과 좌표를 복사 (이미지 자체는 참조)
			face_img, coords = face_det_results[i]
			expanded_results.append([face_img, coords])
	
	return expanded_results[:target_length]

def get_smoothened_boxes(boxes, T):
	for i in range(len(boxes)):
		if i + T > len(boxes):
			window = boxes[len(boxes) - T:]
		else:
			window = boxes[i : i + T]
		boxes[i] = np.mean(window, axis=0)
	return boxes

def face_detect(images, device, face_detector='scrfd', face_det_batch_size=16, pads=[0, 10, 0, 0], nosmooth=False):
	detector = face_detection.FaceAlignment(face_detection.LandmarksType._2D, 
											flip_input=False, device=device,
											face_detector=face_detector)

	batch_size = face_det_batch_size
	
	while 1:
		predictions = []
		try:
			for i in tqdm(range(0, len(images), batch_size)):
				predictions.extend(detector.get_detections_for_batch(np.array(images[i:i + batch_size])))
		except RuntimeError:
			if batch_size == 1: 
				raise RuntimeError('Image too big to run face detection on GPU. Please use the --resize_factor argument')
			batch_size //= 2
			print('Recovering from OOM error; New batch size: {}'.format(batch_size))
			continue
		break

	results = []
	pady1, pady2, padx1, padx2 = pads
	for rect, image in zip(predictions, images):
		if rect is None:
			cv2.imwrite('temp/faulty_frame.jpg', image)
			raise ValueError('Face not detected! Ensure the video contains a face in all the frames.')

		y1 = int(max(0, rect[1] - pady1))
		y2 = int(min(image.shape[0], rect[3] + pady2))
		x1 = int(max(0, rect[0] - padx1))
		x2 = int(min(image.shape[1], rect[2] + padx2))
		
		results.append([x1, y1, x2, y2])

	boxes = np.array(results)
	if not nosmooth: boxes = get_smoothened_boxes(boxes, T=5)
	results = [[image[y1: y2, x1:x2], (y1, y2, x1, x2)] for image, (x1, y1, x2, y2) in zip(images, boxes)]

	del detector
	return results 

def datagen(frames, mels, static=False, box=[-1, -1, -1, -1], face_det_results=None, img_size=96, batch_size=128):
	img_batch, mel_batch, frame_batch, coords_batch = [], [], [], []

	if box[0] == -1:
		if not static:
			face_det_results = face_det_results
		else:
			face_det_results = face_det_results[:1] if face_det_results else []
	else:
		print('Using the specified bounding box instead of face detection...')
		y1, y2, x1, x2 = box
		face_det_results = [[f[y1: y2, x1:x2], (y1, y2, x1, x2)] for f in frames]

	for i, m in enumerate(mels):
		# static 모드가 아니면 인덱스 직접 사용 (이미 확장된 프레임이므로 순환 불필요)
		# static 모드면 첫 프레임만 사용
		if static:
			idx = 0
		else:
			# 프레임이 이미 오디오 길이에 맞춰 확장되었으므로 직접 인덱스 사용
			idx = min(i, len(frames) - 1)
		
		frame_to_save = frames[idx].copy()
		face, coords = face_det_results[idx].copy()

		face = cv2.resize(face, (img_size, img_size))
			
		img_batch.append(face)
		mel_batch.append(m)
		frame_batch.append(frame_to_save)
		coords_batch.append(coords)

		if len(img_batch) >= batch_size:
			img_batch, mel_batch = np.asarray(img_batch), np.asarray(mel_batch)

			img_masked = img_batch.copy()
			img_masked[:, img_size//2:] = 0

			img_batch = np.concatenate((img_masked, img_batch), axis=3) / 255.
			mel_batch = np.reshape(mel_batch, [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1])

			yield img_batch, mel_batch, frame_batch, coords_batch
			img_batch, mel_batch, frame_batch, coords_batch = [], [], [], []

	if len(img_batch) > 0:
		img_batch, mel_batch = np.asarray(img_batch), np.asarray(mel_batch)

		img_masked = img_batch.copy()
		img_masked[:, img_size//2:] = 0

		img_batch = np.concatenate((img_masked, img_batch), axis=3) / 255.
		mel_batch = np.reshape(mel_batch, [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1])

		yield img_batch, mel_batch, frame_batch, coords_batch

def run_wav2lip_inference(
	model,
	face_video_path: str,
	audio_path: str,
	output_path: str,
	device: str = 'cuda',
	wav2lip_batch_size: int = 24,
	face_det_batch_size: int = 12,
	face_detector: str = 'scrfd',
	pads: list = [0, 15, 0, 0],
	resize_factor: int = 1,
	box: list = [-1, -1, -1, -1],
	static: bool = False,
	nosmooth: bool = False,
	video_speed: float = 1.0,
	audio_speed: float = 0.8
):
	"""
	Wav2Lip inference 실행 (모델 재사용)
	
	Args:
		model: 이미 로드된 Wav2Lip 모델
		face_video_path: 얼굴 영상 경로
		audio_path: 오디오 경로
		output_path: 출력 영상 경로
		device: 'cuda' or 'cpu'
		wav2lip_batch_size: Wav2Lip 배치 크기
		face_det_batch_size: 얼굴 감지 배치 크기
		face_detector: 'sfd' or 'scrfd'
		pads: [top, bottom, left, right] 패딩
		resize_factor: 해상도 축소 비율
		box: [y1, y2, x1, x2] 고정 바운딩 박스
		static: 정적 이미지 모드
		nosmooth: 얼굴 감지 스무딩 비활성화
		video_speed: 영상 배속 조절 (1.0 = 정상, 0.5 = 2배 느리게, 2.0 = 2배 빠르게)
		audio_speed: 오디오 배속 조절 (1.0 = 정상, 0.8 = 1.25배 느리게, 0.5 = 2배 느리게)
	"""
	pipeline_start = time.time()  # 전체 파이프라인 시작 시간
	
	# ============================================
	# 0단계: 영상 읽기
	# ============================================
	step_start = time.time()
	fps = 18.0  # 무조건 18fps로 고정
	if os.path.isfile(face_video_path) and face_video_path.split('.')[-1] in ['jpg', 'png', 'jpeg']:
		full_frames = [cv2.imread(face_video_path)]
		static = True
		print(f"[Step 0] Reading image file: {face_video_path}")
	else:
		video_stream = cv2.VideoCapture(face_video_path)
		# 원본 FPS는 읽기만 하고 사용하지 않음 (18fps로 고정)
		original_fps_read = video_stream.get(cv2.CAP_PROP_FPS)
		print(f"[Step 0] Reading video file: {face_video_path}")
		print(f"  - Original video FPS (not used): {original_fps_read:.2f}, using fixed 18.0 fps")

		full_frames = []
		while 1:
			still_reading, frame = video_stream.read()
			if not still_reading:
				video_stream.release()
				break
			
			if resize_factor > 1:
				frame = cv2.resize(frame, (frame.shape[1]//resize_factor, frame.shape[0]//resize_factor))
			full_frames.append(frame)

	step_time = time.time() - step_start
	print(f"[Step 0] Video reading completed: {len(full_frames)} frames in {step_time:.2f}s")

	# ============================================
	# 1단계: 오디오 처리 및 배속 조정
	# ============================================
	step_start = time.time()
	print(f"[Step 1] Audio processing started")
	
	# 1-1. 오디오 변환 (필요한 경우)
	if not audio_path.endswith('.wav'):
		convert_start = time.time()
		print(f"  [1-1] Converting audio to WAV format...")
		temp_wav = 'temp/temp.wav'
		os.makedirs('temp', exist_ok=True)
		command = f'ffmpeg -y -i {audio_path} -strict -2 {temp_wav}'
		subprocess.call(command, shell=platform.system() != 'Windows')
		audio_path = temp_wav
		convert_time = time.time() - convert_start
		print(f"  [1-1] Audio conversion completed in {convert_time:.2f}s")
	else:
		print(f"  [1-1] Audio already in WAV format, skipping conversion")

	# 1-2. 오디오 배속 조정 (느리게 만들기)
	if audio_speed != 1.0:
		speed_start = time.time()
		print(f"  [1-2] Adjusting audio speed to {audio_speed}x (slower)...")
		slowed_audio_path = 'temp/temp_slowed.wav'
		os.makedirs('temp', exist_ok=True)
		# atempo 필터 사용 (0.5 ~ 2.0 범위, 그 이상은 체인 필요)
		if audio_speed < 0.5:
			# 0.5보다 작으면 여러 번 체인
			atempo_value = 0.5
			chain_count = int(np.ceil(np.log(audio_speed) / np.log(0.5)))
			atempo_filter = ','.join(['atempo=0.5'] * chain_count)
		elif audio_speed > 2.0:
			# 2.0보다 크면 여러 번 체인
			atempo_value = 2.0
			chain_count = int(np.ceil(np.log(audio_speed) / np.log(2.0)))
			atempo_filter = ','.join(['atempo=2.0'] * chain_count)
		else:
			atempo_filter = f'atempo={audio_speed}'
		
		command = f'ffmpeg -y -i {audio_path} -af "{atempo_filter}" -strict -2 {slowed_audio_path}'
		subprocess.call(command, shell=platform.system() != 'Windows')
		audio_path = slowed_audio_path
		speed_time = time.time() - speed_start
		print(f"  [1-2] Audio speed adjustment completed in {speed_time:.2f}s")
	else:
		print(f"  [1-2] Audio speed adjustment skipped (audio_speed=1.0)")

	# 1-3. Mel spectrogram 생성
	mel_start = time.time()
	print(f"  [1-3] Generating mel spectrogram...")
	wav = audio.load_wav(audio_path, 16000)
	mel = audio.melspectrogram(wav)
	mel_time = time.time() - mel_start
	print(f"  [1-3] Mel spectrogram generated: shape {mel.shape} in {mel_time:.2f}s")

	if np.isnan(mel.reshape(-1)).sum() > 0:
		raise ValueError('Mel contains nan! Using a TTS voice? Add a small epsilon noise to the wav file and try again')

	# 1-4. Mel chunks 생성 (느려진 오디오 길이 기준)
	chunks_start = time.time()
	print(f"  [1-4] Creating mel chunks...")
	mel_chunks = []
	mel_idx_multiplier = 80./fps  # 원본 FPS 기준
	i = 0
	while 1:
		start_idx = int(i * mel_idx_multiplier)
		if start_idx + mel_step_size > len(mel[0]):
			mel_chunks.append(mel[:, len(mel[0]) - mel_step_size:])
			break
		mel_chunks.append(mel[:, start_idx : start_idx + mel_step_size])
		i += 1
	chunks_time = time.time() - chunks_start
	target_frame_count = len(mel_chunks)
	
	step_time = time.time() - step_start
	print(f"[Step 1] Audio processing completed in {step_time:.2f}s")
	print(f"  - Audio length: {target_frame_count} frames (mel chunks)")
	print(f"  - Original video frames: {len(full_frames)}")

	# ============================================
	# 2단계: 배속 조정된 오디오 길이에 맞춰 영상 길이 조정
	# ============================================
	step_start = time.time()
	print(f"[Step 2] Video frame adjustment started")
	original_frames = full_frames.copy()
	# 원본 FPS는 그대로 유지 (24fps 등)
	
	if len(full_frames) < target_frame_count:
		extend_start = time.time()
		print(f"  [2-1] Extending video frames from {len(full_frames)} to {target_frame_count} to match slowed audio length...")
		full_frames = increase_frames(full_frames, target_frame_count)
		extend_time = time.time() - extend_start
		# FPS는 원본 그대로 유지 (24fps 등) - 빠르게 재생되지 않도록
		print(f"  [2-1] Frame extension completed in {extend_time:.2f}s")
		print(f"  - Maintaining original FPS: {fps:.2f} (frames extended but FPS unchanged)")
	elif len(full_frames) > target_frame_count:
		trim_start = time.time()
		print(f"  [2-1] Trimming video frames from {len(full_frames)} to {target_frame_count} to match audio length...")
		full_frames = full_frames[:target_frame_count]
		trim_time = time.time() - trim_start
		print(f"  [2-1] Frame trimming completed in {trim_time:.2f}s")
		# FPS는 그대로 유지 (프레임 수만 줄임)
	else:
		print(f"  [2-1] Video and audio lengths match perfectly, no adjustment needed")
	
	step_time = time.time() - step_start
	print(f"[Step 2] Video frame adjustment completed in {step_time:.2f}s")
	print(f"  - Final frame count: {len(full_frames)}")

	# ============================================
	# 3단계: 조정된 영상에서 얼굴 탐지 (최적화)
	# ============================================
	step_start = time.time()
	print(f"[Step 3] Face detection started")
	if box[0] == -1:
		if not static:
			# 최적화: 원본 프레임만 얼굴 감지 후 결과 확장
			if len(original_frames) < target_frame_count:
				# 영상이 확장된 경우: 원본만 감지 후 결과 확장
				print(f"  [3-1] Optimized face detection: detecting {len(original_frames)} original frames, then expanding results...")
				face_det_start = time.time()
				face_det_results_original = face_detect(original_frames, device, face_detector, face_det_batch_size, pads, nosmooth)
				face_det_time = time.time() - face_det_start
				print(f"  [3-1] Face detection completed in {face_det_time:.2f}s")
				
				expand_start = time.time()
				print(f"  [3-2] Expanding face detection results from {len(original_frames)} to {target_frame_count}...")
				face_det_results = expand_face_det_results(face_det_results_original, target_frame_count)
				expand_time = time.time() - expand_start
				print(f"  [3-2] Result expansion completed in {expand_time:.2f}s")
			else:
				# 영상이 잘린 경우: 잘린 프레임에 대해 감지
				print(f"  [3-1] Face detection on {len(full_frames)} frames...")
				face_det_start = time.time()
				face_det_results = face_detect(full_frames, device, face_detector, face_det_batch_size, pads, nosmooth)
				face_det_time = time.time() - face_det_start
				print(f"  [3-1] Face detection completed in {face_det_time:.2f}s")
		else:
			print(f"  [3-1] Static mode: detecting face on first frame only...")
			face_det_start = time.time()
			face_det_results = face_detect([full_frames[0]], device, face_detector, face_det_batch_size, pads, nosmooth)
			face_det_time = time.time() - face_det_start
			print(f"  [3-1] Face detection completed in {face_det_time:.2f}s")
			# static 모드에서도 확장 필요
			if target_frame_count > 1:
				expand_start = time.time()
				print(f"  [3-2] Expanding face detection results from 1 to {target_frame_count}...")
				face_det_results = expand_face_det_results(face_det_results, target_frame_count)
				expand_time = time.time() - expand_start
				print(f"  [3-2] Result expansion completed in {expand_time:.2f}s")
	else:
		print('  [3-1] Using the specified bounding box instead of face detection...')
		bbox_start = time.time()
		y1, y2, x1, x2 = box
		face_det_results = [[f[y1: y2, x1:x2], (y1, y2, x1, x2)] for f in full_frames]
		bbox_time = time.time() - bbox_start
		print(f"  [3-1] Bounding box extraction completed in {bbox_time:.2f}s")
	
	step_time = time.time() - step_start
	print(f"[Step 3] Face detection completed in {step_time:.2f}s")
	print(f"  - Total face detection results: {len(face_det_results)}")

	# ============================================
	# 4단계: Inference 실행
	# ============================================
	step_start = time.time()
	print(f"[Step 4] Wav2Lip inference started")
	batch_size = wav2lip_batch_size
	gen = datagen(full_frames.copy(), mel_chunks, static, box, face_det_results, img_size=96, batch_size=batch_size)
	
	frame_h, frame_w = full_frames[0].shape[:-1]
	os.makedirs('temp', exist_ok=True)
	
	# FPS 하드코딩: 무조건 18fps
	fps = 18.0
	print(f"  - Video output settings: {frame_w}x{frame_h} @ {fps:.2f}fps")
	out = cv2.VideoWriter('temp/result.avi', 
							cv2.VideoWriter_fourcc(*'DIVX'), fps, (frame_w, frame_h))

	inference_start = time.time()
	postprocess_start = None
	postprocess_time = 0
	
	for i, (img_batch, mel_batch, frames, coords) in enumerate(tqdm(gen, 
										total=int(np.ceil(float(len(mel_chunks))/batch_size)))):
		if i == 0:
			batch_start = time.time()
		
		# 4-1. 입력 변환
		if i == 0:
			convert_start = time.time()
		if next(model.parameters()).dtype == torch.float16:
			img_batch = torch.HalfTensor(np.transpose(img_batch, (0, 3, 1, 2))).to(device)
			mel_batch = torch.HalfTensor(np.transpose(mel_batch, (0, 3, 1, 2))).to(device)
		else:
			img_batch = torch.FloatTensor(np.transpose(img_batch, (0, 3, 1, 2))).to(device)
			mel_batch = torch.FloatTensor(np.transpose(mel_batch, (0, 3, 1, 2))).to(device)
		if i == 0:
			convert_time = time.time() - convert_start
			print(f"  [4-1] First batch input conversion: {convert_time:.3f}s")

		# 4-2. 모델 Inference
		if i == 0:
			model_start = time.time()
		with torch.no_grad():
			if device == 'cuda' and next(model.parameters()).dtype == torch.float16:
				with torch.amp.autocast('cuda'):
					pred = model(mel_batch, img_batch)
			else:
				pred = model(mel_batch, img_batch)
		if i == 0:
			model_time = time.time() - model_start
			print(f"  [4-2] First batch model inference: {model_time:.3f}s")

		# 4-3. 후처리 시작 시간 측정
		if postprocess_start is None:
			postprocess_start = time.time()
		
		# CUDA 텐서를 CPU로 이동 후 numpy로 변환
		pred = pred.cpu().numpy().transpose(0, 2, 3, 1) * 255.
		
		for p, f, c in zip(pred, frames, coords):
			y1, y2, x1, x2 = c
			y1, y2, x1, x2 = int(y1), int(y2), int(x1), int(x2)
			
			target_width = x2 - x1
			target_height = y2 - y1
			p = cv2.resize(p.astype(np.uint8), (target_width, target_height))
			
			# 페더링
			feather_amount = min(15, max(5, target_width // 15, target_height // 15))
			
			if feather_amount > 0:
				mask = np.ones((target_height, target_width), dtype=np.float32)
				fade_range = np.arange(feather_amount, dtype=np.float32) / feather_amount
				
				mask[:feather_amount, :] *= fade_range[:, np.newaxis]
				mask[-feather_amount:, :] *= fade_range[::-1, np.newaxis]
				mask[:, :feather_amount] *= fade_range[np.newaxis, :]
				mask[:, -feather_amount:] *= fade_range[::-1, np.newaxis].T
				
				mask = mask[:, :, np.newaxis]
				original_region = f[y1:y2, x1:x2].astype(np.float32)
				blended = (p.astype(np.float32) * mask + original_region * (1 - mask)).astype(np.uint8)
				
				f[y1:y2, x1:x2] = blended
			else:
				f[y1:y2, x1:x2] = p
			
			out.write(f)
	
	postprocess_time = time.time() - postprocess_start if postprocess_start else 0
	inference_time = time.time() - inference_start
	out.release()
	
	step_time = time.time() - step_start
	print(f"[Step 4] Wav2Lip inference completed in {step_time:.2f}s")
	print(f"  - Total inference time: {inference_time:.2f}s")
	print(f"  - Post-processing time: {postprocess_time:.2f}s")
	print(f"  - Processed {len(mel_chunks)} frames in {int(np.ceil(float(len(mel_chunks))/batch_size))} batches")

	# ============================================
	# 5단계: 오디오 합성
	# ============================================
	step_start = time.time()
	print(f"[Step 5] Audio-video synthesis started")
	command = f'ffmpeg -y -i {audio_path} -i temp/result.avi -strict -2 -q:v 1 {output_path}'
	subprocess.call(command, shell=platform.system() != 'Windows')
	step_time = time.time() - step_start
	print(f"[Step 5] Audio-video synthesis completed in {step_time:.2f}s")
	
	total_time = time.time() - pipeline_start
	print(f"\n[Summary] Output saved to: {output_path}")
	print(f"  - Total pipeline time: {total_time:.2f}s")

