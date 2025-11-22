from os import listdir, path
import numpy as np
import scipy, cv2, os, sys, argparse, audio
import json, subprocess, random, string
from tqdm import tqdm
from glob import glob
import torch, face_detection
from models import Wav2Lip
import platform

parser = argparse.ArgumentParser(description='Inference code to lip-sync videos in the wild using Wav2Lip models')

parser.add_argument('--checkpoint_path', type=str, 
					help='Name of saved checkpoint to load weights from', required=True)

parser.add_argument('--face', type=str, 
					help='Filepath of video/image that contains faces to use', required=True)
parser.add_argument('--audio', type=str, 
					help='Filepath of video/audio file to use as raw audio source', required=True)
parser.add_argument('--outfile', type=str, help='Video path to save result. See default for an e.g.', 
								default='results/result_voice.mp4')

parser.add_argument('--static', type=bool, 
					help='If True, then use only first video frame for inference', default=False)
parser.add_argument('--fps', type=float, help='Can be specified only if input is a static image (default: 25)', 
					default=25., required=False)

parser.add_argument('--pads', nargs='+', type=int, default=[0, 10, 0, 0], 
					help='Padding (top, bottom, left, right). Please adjust to include chin at least')

parser.add_argument('--face_det_batch_size', type=int, 
					help='Batch size for face detection', default=16)
parser.add_argument('--wav2lip_batch_size', type=int, help='Batch size for Wav2Lip model(s)', default=128)

parser.add_argument('--resize_factor', default=1, type=int, 
			help='Reduce the resolution by this factor. Sometimes, best results are obtained at 480p or 720p')

parser.add_argument('--crop', nargs='+', type=int, default=[0, -1, 0, -1], 
					help='Crop video to a smaller region (top, bottom, left, right). Applied after resize_factor and rotate arg. ' 
					'Useful if multiple face present. -1 implies the value will be auto-inferred based on height, width')

parser.add_argument('--box', nargs='+', type=int, default=[-1, -1, -1, -1], 
					help='Specify a constant bounding box for the face. Use only as a last resort if the face is not detected.'
					'Also, might work only if the face is not moving around much. Syntax: (top, bottom, left, right).')

parser.add_argument('--rotate', default=False, action='store_true',
					help='Sometimes videos taken from a phone can be flipped 90deg. If true, will flip video right by 90deg.'
					'Use if you get a flipped result, despite feeding a normal looking video')

parser.add_argument('--nosmooth', default=False, action='store_true',
					help='Prevent smoothing face detections over a short temporal window')

parser.add_argument('--face_detector', type=str, default='scrfd',
					help='Face detector to use: sfd (S3FD, slower) or scrfd (SCRFD, faster GPU)', choices=['sfd', 'scrfd'])

args = parser.parse_args()
args.img_size = 96

if os.path.isfile(args.face) and args.face.split('.')[1] in ['jpg', 'png', 'jpeg']:
	args.static = True

def get_smoothened_boxes(boxes, T):
	for i in range(len(boxes)):
		if i + T > len(boxes):
			window = boxes[len(boxes) - T:]
		else:
			window = boxes[i : i + T]
		boxes[i] = np.mean(window, axis=0)
	return boxes

def face_detect(images):
	detector = face_detection.FaceAlignment(face_detection.LandmarksType._2D, 
											flip_input=False, device=device,
											face_detector=args.face_detector)

	batch_size = args.face_det_batch_size
	
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
	pady1, pady2, padx1, padx2 = args.pads
	for rect, image in zip(predictions, images):
		if rect is None:
			cv2.imwrite('temp/faulty_frame.jpg', image) # check this frame where the face was not detected.
			raise ValueError('Face not detected! Ensure the video contains a face in all the frames.')

		# 좌표를 정수로 명시적 변환하여 경계 오차 방지
		y1 = int(max(0, rect[1] - pady1))
		y2 = int(min(image.shape[0], rect[3] + pady2))
		x1 = int(max(0, rect[0] - padx1))
		x2 = int(min(image.shape[1], rect[2] + padx2))
		
		results.append([x1, y1, x2, y2])

	boxes = np.array(results)
	if not args.nosmooth: boxes = get_smoothened_boxes(boxes, T=5)
	results = [[image[y1: y2, x1:x2], (y1, y2, x1, x2)] for image, (x1, y1, x2, y2) in zip(images, boxes)]

	del detector
	return results 

def datagen(frames, mels, original_frames=None):
	img_batch, mel_batch, frame_batch, coords_batch = [], [], [], []

	# 최적화: 원본 프레임만 얼굴 감지 후 결과 확장
	if args.box[0] == -1:
		if not args.static:
			# 원본 프레임이 제공되고 확장된 경우 최적화
			if original_frames is not None and len(original_frames) < len(frames):
				print("Optimized face detection: detecting {} original frames, then expanding results".format(len(original_frames)))
				face_det_results_original = face_detect(original_frames)
				face_det_results = expand_face_det_results(face_det_results_original, len(frames))
			else:
				face_det_results = face_detect(frames) # BGR2RGB for CNN face detection
		else:
			face_det_results_original = face_detect([frames[0]])
			if len(frames) > 1:
				face_det_results = expand_face_det_results(face_det_results_original, len(frames))
			else:
				face_det_results = face_det_results_original
	else:
		print('Using the specified bounding box instead of face detection...')
		y1, y2, x1, x2 = args.box
		face_det_results = [[f[y1: y2, x1:x2], (y1, y2, x1, x2)] for f in frames]

	for i, m in enumerate(mels):
		# static 모드가 아니면 인덱스 직접 사용 (이미 확장된 프레임이므로 순환 불필요)
		# static 모드면 첫 프레임만 사용
		if args.static:
			idx = 0
		else:
			# 프레임이 이미 오디오 길이에 맞춰 확장되었으므로 직접 인덱스 사용
			idx = min(i, len(frames) - 1)
		
		frame_to_save = frames[idx].copy()
		face, coords = face_det_results[idx].copy()

		face = cv2.resize(face, (args.img_size, args.img_size))
			
		img_batch.append(face)
		mel_batch.append(m)
		frame_batch.append(frame_to_save)
		coords_batch.append(coords)

		if len(img_batch) >= args.wav2lip_batch_size:
			img_batch, mel_batch = np.asarray(img_batch), np.asarray(mel_batch)

			img_masked = img_batch.copy()
			img_masked[:, args.img_size//2:] = 0

			img_batch = np.concatenate((img_masked, img_batch), axis=3) / 255.
			mel_batch = np.reshape(mel_batch, [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1])

			yield img_batch, mel_batch, frame_batch, coords_batch
			img_batch, mel_batch, frame_batch, coords_batch = [], [], [], []

	if len(img_batch) > 0:
		img_batch, mel_batch = np.asarray(img_batch), np.asarray(mel_batch)

		img_masked = img_batch.copy()
		img_masked[:, args.img_size//2:] = 0

		img_batch = np.concatenate((img_masked, img_batch), axis=3) / 255.
		mel_batch = np.reshape(mel_batch, [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1])

		yield img_batch, mel_batch, frame_batch, coords_batch

mel_step_size = 16
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print('Using {} for inference.'.format(device))

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
	
	# 벡터화된 확장 수행
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

def _load(checkpoint_path):
	if device == 'cuda':
		checkpoint = torch.load(checkpoint_path)
	else:
		checkpoint = torch.load(checkpoint_path,
								map_location=lambda storage, loc: storage)
	return checkpoint

def load_model(path, use_half_precision=True):
	model = Wav2Lip()
	print("Load checkpoint from: {}".format(path))
	checkpoint = _load(path)
	s = checkpoint["state_dict"]
	new_s = {}
	for k, v in s.items():
		new_s[k.replace('module.', '')] = v
	model.load_state_dict(new_s)

	model = model.to(device)
	
	# Mixed Precision (FP16) 최적화 - L4 GPU는 Tensor Core 지원으로 2배 빠름
	if device == 'cuda' and use_half_precision:
		try:
			model = model.half()  # FP16으로 변환
			print("Model converted to FP16 (half precision) for faster inference")
		except Exception as e:
			print(f"Warning: Could not convert to FP16: {e}, using FP32")
	
	# PyTorch 2.0+ compile 최적화 (가능한 경우)
	try:
		if hasattr(torch, 'compile') and device == 'cuda':
			model = torch.compile(model, mode='reduce-overhead')
			print("Model compiled with torch.compile for faster inference")
	except Exception as e:
		print(f"Warning: torch.compile not available: {e}")
	
	return model.eval()

def main():
	if not os.path.isfile(args.face):
		raise ValueError('--face argument must be a valid path to video/image file')

	elif args.face.split('.')[1] in ['jpg', 'png', 'jpeg']:
		full_frames = [cv2.imread(args.face)]
		fps = args.fps

	else:
		video_stream = cv2.VideoCapture(args.face)
		fps = video_stream.get(cv2.CAP_PROP_FPS)

		print('Reading video frames...')

		full_frames = []
		while 1:
			still_reading, frame = video_stream.read()
			if not still_reading:
				video_stream.release()
				break
			if args.resize_factor > 1:
				frame = cv2.resize(frame, (frame.shape[1]//args.resize_factor, frame.shape[0]//args.resize_factor))

			if args.rotate:
				frame = cv2.rotate(frame, cv2.cv2.ROTATE_90_CLOCKWISE)

			y1, y2, x1, x2 = args.crop
			if x2 == -1: x2 = frame.shape[1]
			if y2 == -1: y2 = frame.shape[0]

			frame = frame[y1:y2, x1:x2]

			full_frames.append(frame)

	print ("Number of frames available for inference: "+str(len(full_frames)))

	# ============================================
	# 1단계: 오디오 처리 및 배속 조정
	# ============================================
	if not args.audio.endswith('.wav'):
		print('Extracting raw audio...')
		command = 'ffmpeg -y -i {} -strict -2 {}'.format(args.audio, 'temp/temp.wav')
		subprocess.call(command, shell=True)
		args.audio = 'temp/temp.wav'

	# 오디오 배속 조정 (기본값 0.8 = 1.25배 느리게)
	audio_speed = getattr(args, 'audio_speed', 0.8)
	if audio_speed != 1.0:
		print('Adjusting audio speed to {}x (slower)'.format(audio_speed))
		slowed_audio_path = 'temp/temp_slowed.wav'
		os.makedirs('temp', exist_ok=True)
		# atempo 필터 사용 (0.5 ~ 2.0 범위, 그 이상은 체인 필요)
		if audio_speed < 0.5:
			chain_count = int(np.ceil(np.log(audio_speed) / np.log(0.5)))
			atempo_filter = ','.join(['atempo=0.5'] * chain_count)
		elif audio_speed > 2.0:
			chain_count = int(np.ceil(np.log(audio_speed) / np.log(2.0)))
			atempo_filter = ','.join(['atempo=2.0'] * chain_count)
		else:
			atempo_filter = 'atempo={}'.format(audio_speed)
		
		command = 'ffmpeg -y -i {} -af "{}" -strict -2 {}'.format(args.audio, atempo_filter, slowed_audio_path)
		subprocess.call(command, shell=True)
		args.audio = slowed_audio_path
		print('Audio slowed to {}x speed'.format(audio_speed))

	wav = audio.load_wav(args.audio, 16000)
	mel = audio.melspectrogram(wav)
	print(mel.shape)

	if np.isnan(mel.reshape(-1)).sum() > 0:
		raise ValueError('Mel contains nan! Using a TTS voice? Add a small epsilon noise to the wav file and try again')

	# Mel chunks 생성 (느려진 오디오 길이 기준)
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

	target_frame_count = len(mel_chunks)
	print("Audio length: {} frames (mel chunks)".format(target_frame_count))
	print("Original video frames: {}".format(len(full_frames)))

	# ============================================
	# 2단계: 배속 조정된 오디오 길이에 맞춰 영상 길이 조정
	# ============================================
	original_frames = full_frames.copy()
	# 원본 FPS는 그대로 유지 (24fps 등)
	
	if len(full_frames) < target_frame_count:
		print("Extending video frames from {} to {} to match slowed audio length".format(len(full_frames), target_frame_count))
		full_frames = increase_frames(full_frames, target_frame_count)
		# FPS는 원본 그대로 유지 (24fps 등) - 빠르게 재생되지 않도록
		print("Maintaining original FPS: {:.2f} (frames extended but FPS unchanged)".format(fps))
	elif len(full_frames) > target_frame_count:
		print("Trimming video frames from {} to {} to match audio length".format(len(full_frames), target_frame_count))
		full_frames = full_frames[:target_frame_count]
		# FPS는 그대로 유지 (프레임 수만 줄임)
	else:
		print("Video and audio lengths match perfectly")

	# ============================================
	# 3단계: 조정된 영상에서 얼굴 탐지 (최적화)
	# ============================================
	# datagen 함수 내부에서 얼굴 감지 수행
	# 최적화: 원본 프레임만 감지 후 결과 확장
	batch_size = args.wav2lip_batch_size
	gen = datagen(full_frames.copy(), mel_chunks, original_frames=original_frames if len(original_frames) < target_frame_count else None)

	for i, (img_batch, mel_batch, frames, coords) in enumerate(tqdm(gen, 
											total=int(np.ceil(float(len(mel_chunks))/batch_size)))):
		if i == 0:
			model = load_model(args.checkpoint_path)
			print ("Model loaded")

			frame_h, frame_w = full_frames[0].shape[:-1]
			out = cv2.VideoWriter('temp/result.avi', 
									cv2.VideoWriter_fourcc(*'DIVX'), fps, (frame_w, frame_h))

		# Mixed Precision 입력 변환 (FP16 모델 사용 시)
		if next(model.parameters()).dtype == torch.float16:
			img_batch = torch.HalfTensor(np.transpose(img_batch, (0, 3, 1, 2))).to(device)
			mel_batch = torch.HalfTensor(np.transpose(mel_batch, (0, 3, 1, 2))).to(device)
		else:
			img_batch = torch.FloatTensor(np.transpose(img_batch, (0, 3, 1, 2))).to(device)
			mel_batch = torch.FloatTensor(np.transpose(mel_batch, (0, 3, 1, 2))).to(device)

		# CUDA 스트림 최적화 + Mixed Precision
		with torch.no_grad():
			if device == 'cuda' and next(model.parameters()).dtype == torch.float16:
				# FP16 autocast로 추가 최적화 (deprecated 경고 수정)
				with torch.amp.autocast('cuda'):
					pred = model(mel_batch, img_batch)
			else:
				pred = model(mel_batch, img_batch)

		pred = pred.cpu().numpy().transpose(0, 2, 3, 1) * 255.
		
		for p, f, c in zip(pred, frames, coords):
			y1, y2, x1, x2 = c
			# 좌표를 정수로 변환 (이미 정수여야 하지만 명시적 변환)
			y1, y2, x1, x2 = int(y1), int(y2), int(x1), int(x2)
			
			# 정확한 크기로 리사이즈
			target_width = x2 - x1
			target_height = y2 - y1
			p = cv2.resize(p.astype(np.uint8), (target_width, target_height))
			
			# 페더링을 적용하여 경계를 부드럽게 (벡터화 최적화)
			# 가장자리 픽셀 수 계산 (영역의 약 7% 또는 최대 15픽셀, 품질 우선)
			feather_amount = min(15, max(5, target_width // 15, target_height // 15))
			
			if feather_amount > 0:
				# 벡터화된 페더링 마스크 생성 (Python 루프 제거)
				mask = np.ones((target_height, target_width), dtype=np.float32)
				
				# NumPy 벡터화로 페더링 적용 (훨씬 빠름)
				fade_range = np.arange(feather_amount, dtype=np.float32) / feather_amount
				
				# 위쪽/아래쪽 가장자리 (올바른 브로드캐스팅)
				mask[:feather_amount, :] *= fade_range[:, np.newaxis]  # (feather_amount, 1) -> (feather_amount, width)
				mask[-feather_amount:, :] *= fade_range[::-1, np.newaxis]  # (feather_amount, 1) -> (feather_amount, width)
				
				# 왼쪽/오른쪽 가장자리 (올바른 브로드캐스팅)
				mask[:, :feather_amount] *= fade_range[np.newaxis, :]  # (1, feather_amount) -> (height, feather_amount)
				mask[:, -feather_amount:] *= fade_range[::-1, np.newaxis].T  # transpose로 (1, feather_amount) -> (height, feather_amount)
				
				# 알파 블렌딩 (벡터화)
				mask = mask[:, :, np.newaxis]  # (H, W, 1)
				original_region = f[y1:y2, x1:x2].astype(np.float32)
				blended = (p.astype(np.float32) * mask + original_region * (1 - mask)).astype(np.uint8)
				
				f[y1:y2, x1:x2] = blended
			else:
				# 페더링 없이 직접 대입
				f[y1:y2, x1:x2] = p
			
			out.write(f)

	out.release()

	command = 'ffmpeg -y -i {} -i {} -strict -2 -q:v 1 {}'.format(args.audio, 'temp/result.avi', args.outfile)
	subprocess.call(command, shell=platform.system() != 'Windows')

if __name__ == '__main__':
	main()
