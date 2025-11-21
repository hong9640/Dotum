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

mel_step_size = 16

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
		idx = 0 if static else i%len(frames)
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
	nosmooth: bool = False
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
	"""
	# 영상 읽기
	if os.path.isfile(face_video_path) and face_video_path.split('.')[-1] in ['jpg', 'png', 'jpeg']:
		full_frames = [cv2.imread(face_video_path)]
		fps = 25.0
		static = True
	else:
		video_stream = cv2.VideoCapture(face_video_path)
		fps = video_stream.get(cv2.CAP_PROP_FPS)

		full_frames = []
		while 1:
			still_reading, frame = video_stream.read()
			if not still_reading:
				video_stream.release()
				break
			if resize_factor > 1:
				frame = cv2.resize(frame, (frame.shape[1]//resize_factor, frame.shape[0]//resize_factor))
			full_frames.append(frame)

	print(f"Number of frames available for inference: {len(full_frames)}")

	# 오디오 처리
	if not audio_path.endswith('.wav'):
		print('Extracting raw audio...')
		temp_wav = 'temp/temp.wav'
		os.makedirs('temp', exist_ok=True)
		command = f'ffmpeg -y -i {audio_path} -strict -2 {temp_wav}'
		subprocess.call(command, shell=platform.system() != 'Windows')
		audio_path = temp_wav

	wav = audio.load_wav(audio_path, 16000)
	mel = audio.melspectrogram(wav)

	if np.isnan(mel.reshape(-1)).sum() > 0:
		raise ValueError('Mel contains nan! Using a TTS voice? Add a small epsilon noise to the wav file and try again')

	# Mel chunks 생성
	mel_chunks = []
	mel_idx_multiplier = 80./fps 
	i = 0
	while 1:
		start_idx = int(i * mel_idx_multiplier)
		if start_idx + mel_step_size > len(mel[0]):
			mel_chunks.append(mel[:, len(mel[0]) - mel_step_size:])
			break
		mel_chunks.append(mel[:, start_idx : start_idx + mel_step_size])
		i += 1

	print(f"Length of mel chunks: {len(mel_chunks)}")
	full_frames = full_frames[:len(mel_chunks)]

	# 얼굴 감지
	if box[0] == -1:
		if not static:
			face_det_results = face_detect(full_frames, device, face_detector, face_det_batch_size, pads, nosmooth)
		else:
			face_det_results = face_detect([full_frames[0]], device, face_detector, face_det_batch_size, pads, nosmooth)
	else:
		print('Using the specified bounding box instead of face detection...')
		y1, y2, x1, x2 = box
		face_det_results = [[f[y1: y2, x1:x2], (y1, y2, x1, x2)] for f in full_frames]

	# Inference 실행
	batch_size = wav2lip_batch_size
	gen = datagen(full_frames.copy(), mel_chunks, static, box, face_det_results, img_size=96, batch_size=batch_size)
	
	frame_h, frame_w = full_frames[0].shape[:-1]
	os.makedirs('temp', exist_ok=True)
	out = cv2.VideoWriter('temp/result.avi', 
							cv2.VideoWriter_fourcc(*'DIVX'), fps, (frame_w, frame_h))

	for i, (img_batch, mel_batch, frames, coords) in enumerate(tqdm(gen, 
										total=int(np.ceil(float(len(mel_chunks))/batch_size)))):
		# Mixed Precision 입력 변환
		if next(model.parameters()).dtype == torch.float16:
			img_batch = torch.HalfTensor(np.transpose(img_batch, (0, 3, 1, 2))).to(device)
			mel_batch = torch.HalfTensor(np.transpose(mel_batch, (0, 3, 1, 2))).to(device)
		else:
			img_batch = torch.FloatTensor(np.transpose(img_batch, (0, 3, 1, 2))).to(device)
			mel_batch = torch.FloatTensor(np.transpose(mel_batch, (0, 3, 1, 2))).to(device)

		# Inference
		with torch.no_grad():
			if device == 'cuda' and next(model.parameters()).dtype == torch.float16:
				with torch.amp.autocast('cuda'):
					pred = model(mel_batch, img_batch)
			else:
				pred = model(mel_batch, img_batch)

		pred = pred.cpu().numpy().transpose(0, 2, 3, 1) * 255.
		
		# 후처리
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

	out.release()

	# 오디오 합성
	command = f'ffmpeg -y -i {audio_path} -i temp/result.avi -strict -2 -q:v 1 {output_path}'
	subprocess.call(command, shell=platform.system() != 'Windows')
	
	print(f"Output saved to: {output_path}")

