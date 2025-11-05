"""
FreeVC GPU 최적화 모듈
- GPU 기반 모델 사전 로드 및 캐싱
- subprocess 제거
- 직접 추론 실행
- CUDA 최적화
"""

import os
import sys
import torch
import librosa
import numpy as np
import logging
import warnings
from scipy.io.wavfile import write
from typing import Optional, Tuple
from pathlib import Path

# 불필요한 로그 억제
logging.getLogger('numba').setLevel(logging.WARNING)
logging.getLogger('numba.core').setLevel(logging.WARNING)
logging.getLogger('numba.core.ssa').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.INFO)

# Torch 경고 억제
warnings.filterwarnings('ignore', category=UserWarning, module='torch')
warnings.filterwarnings('ignore', message='.*stft with return_complex.*')

# FreeVC 모듈 경로 추가
from api.core.config import settings
from api.core.logger import logger

# 전역 모델 캐시
_freevc_models = {
    "net_g": None,
    "cmodel": None,
    "smodel": None,
    "hps": None,
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "loaded": False
}


def get_device():
    """사용 가능한 디바이스 반환"""
    if torch.cuda.is_available():
        device = "cuda"
        logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    else:
        device = "cpu"
        logger.warning("GPU not available, using CPU")
    return device


def load_freevc_models(force_reload: bool = False):
    """
    FreeVC 모델들을 메모리에 로드 (1회만) - GPU 버전
    
    Args:
        force_reload: 강제 재로드 여부
    """
    global _freevc_models
    
    if _freevc_models["loaded"] and not force_reload:
        logger.info("FreeVC models already loaded, skipping...")
        return
    
    try:
        # 디바이스 설정
        device = get_device()
        _freevc_models["device"] = device
        
        # FreeVC 경로를 Python path에 추가
        freevc_path = settings.LOCAL_FREEVC_PATH
        if freevc_path not in sys.path:
            sys.path.insert(0, freevc_path)
        
        # GPU 버전 모듈 임포트 (utils.py 사용)
        if device == "cuda":
            import utils  # GPU 버전
        else:
            import utils_cpu as utils  # CPU 폴백
            
        from models import SynthesizerTrn
        from speaker_encoder.voice_encoder import SpeakerEncoder
        
        logger.info(f"Loading FreeVC models on {device.upper()}...")
        start_time = __import__('time').time()
        
        # 1. 설정 파일 로드
        config_path = os.path.join(freevc_path, "configs", "freevc-s.json")
        model_path = os.path.join(freevc_path, "checkpoints", "freevc-s.pth")
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config not found: {config_path}")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        hps = utils.get_hparams_from_file(config_path)
        _freevc_models["hps"] = hps
        
        # 2. SynthesizerTrn 로드 (GPU 지원)
        logger.info(f"  Loading SynthesizerTrn on {device.upper()}...")
        net_g = SynthesizerTrn(
            hps.data.filter_length // 2 + 1,
            hps.train.segment_size // hps.data.hop_length,
            **hps.model
        )
        
        if device == "cuda":
            net_g = net_g.cuda()
        else:
            net_g = net_g.cpu()
            
        net_g.eval()
        
        # 체크포인트 로드
        utils.load_checkpoint(model_path, net_g, None, True)
        _freevc_models["net_g"] = net_g
        logger.info(f"  ✓ SynthesizerTrn loaded on {device.upper()}")
        
        # 3. WavLM 로드 (가장 무거움!) - GPU 가속!
        logger.info("  Loading WavLM (this may take a while)...")
        # 작업 디렉토리를 FreeVC 경로로 일시 변경 (상대 경로 문제 해결)
        original_cwd = os.getcwd()
        os.chdir(freevc_path)
        try:
            # GPU ID 전달 (0 = CUDA:0, -1 = CPU)
            cmodel = utils.get_cmodel(0 if device == "cuda" else -1)
            _freevc_models["cmodel"] = cmodel
            logger.info(f"  ✓ WavLM loaded on {device.upper()}")
        finally:
            os.chdir(original_cwd)
        
        # 4. Speaker Encoder 로드 (조건부)
        if hps.model.use_spk:
            logger.info("  Loading SpeakerEncoder...")
            speaker_encoder_path = os.path.join(
                freevc_path,
                "speaker_encoder",
                "ckpt",
                "pretrained_bak_5805000.pt"
            )
            if not os.path.exists(speaker_encoder_path):
                raise FileNotFoundError(f"Speaker encoder not found: {speaker_encoder_path}")
            
            smodel = SpeakerEncoder(speaker_encoder_path)
            _freevc_models["smodel"] = smodel
            logger.info("  ✓ SpeakerEncoder loaded")
        
        _freevc_models["loaded"] = True
        
        elapsed = __import__('time').time() - start_time
        logger.info(f"FreeVC models loaded successfully in {elapsed:.2f}s on {device.upper()}")
        
        # GPU 메모리 상태 로깅
        if device == "cuda":
            allocated = torch.cuda.memory_allocated(0) / 1024**3
            reserved = torch.cuda.memory_reserved(0) / 1024**3
            logger.info(f"GPU memory allocated: {allocated:.2f} GB, reserved: {reserved:.2f} GB")
        
    except Exception as e:
        logger.error(f"Failed to load FreeVC models: {e}")
        raise


def infer_freevc(
    src_audio_path: str,
    ref_audio_path: str,
    output_path: str
) -> bool:
    """
    FreeVC 추론 실행 (캐시된 모델 사용) - GPU 버전
    
    Args:
        src_audio_path: 원본 오디오 경로
        ref_audio_path: 참조 오디오 경로
        output_path: 출력 파일 경로
        
    Returns:
        bool: 성공 여부
    """
    global _freevc_models
    
    # 모델이 로드되지 않았으면 로드
    if not _freevc_models["loaded"]:
        load_freevc_models()
    
    try:
        # FreeVC 모듈 임포트
        freevc_path = settings.LOCAL_FREEVC_PATH
        if freevc_path not in sys.path:
            sys.path.insert(0, freevc_path)
        
        # 디바이스에 맞는 utils 임포트
        device = _freevc_models["device"]
        if device == "cuda":
            import utils  # GPU 버전
        else:
            import utils_cpu as utils  # CPU 폴백
            
        from mel_processing import mel_spectrogram_torch
        
        # 캐시된 모델 가져오기
        net_g = _freevc_models["net_g"]
        cmodel = _freevc_models["cmodel"]
        smodel = _freevc_models["smodel"]
        hps = _freevc_models["hps"]
        
        logger.info(f"Running FreeVC inference on {device.upper()} (optimized)")
        logger.info(f"  src: {src_audio_path}")
        logger.info(f"  ref: {ref_audio_path}")
        
        # 작업 디렉토리를 FreeVC 경로로 변경 (상대 경로 문제 해결)
        original_cwd = os.getcwd()
        os.chdir(freevc_path)
        
        try:
            with torch.no_grad():
                # 1. 참조 오디오 로드 (target)
                wav_tgt, _ = librosa.load(ref_audio_path, sr=hps.data.sampling_rate)
                wav_tgt, _ = librosa.effects.trim(wav_tgt, top_db=20)
                
                if hps.model.use_spk:
                    # Speaker embedding 추출
                    g_tgt = smodel.embed_utterance(wav_tgt)
                    g_tgt = torch.from_numpy(g_tgt).unsqueeze(0)
                    if device == "cuda":
                        g_tgt = g_tgt.cuda()
                else:
                    # Mel spectrogram 추출
                    wav_tgt = torch.from_numpy(wav_tgt).unsqueeze(0)
                    if device == "cuda":
                        wav_tgt = wav_tgt.cuda()
                    else:
                        wav_tgt = wav_tgt.cpu()
                        
                    mel_tgt = mel_spectrogram_torch(
                        wav_tgt,
                        hps.data.filter_length,
                        hps.data.n_mel_channels,
                        hps.data.sampling_rate,
                        hps.data.hop_length,
                        hps.data.win_length,
                        hps.data.mel_fmin,
                        hps.data.mel_fmax
                    )
                
                # 2. 원본 오디오 로드 (source)
                wav_src, _ = librosa.load(src_audio_path, sr=hps.data.sampling_rate)
                wav_src = torch.from_numpy(wav_src).unsqueeze(0)
                if device == "cuda":
                    wav_src = wav_src.cuda()
                else:
                    wav_src = wav_src.cpu()
                
                # 3. Content 추출 (WavLM) - GPU 가속!
                c = utils.get_content(cmodel, wav_src)
                
                # 4. 추론 실행 - GPU 가속!
                if hps.model.use_spk:
                    audio = net_g.infer(c, g=g_tgt)
                else:
                    audio = net_g.infer(c, mel=mel_tgt)
                
                # 5. 결과 저장
                audio = audio[0][0].data.cpu().float().numpy()
                
                # 출력 디렉토리 생성
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                write(output_path, hps.data.sampling_rate, audio)
                logger.info(f"FreeVC inference completed: {output_path}")
                
                return True
        finally:
            # 작업 디렉토리 복원
            os.chdir(original_cwd)
            
    except Exception as e:
        logger.error(f"FreeVC inference failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def unload_freevc_models():
    """
    메모리에서 FreeVC 모델 언로드
    """
    global _freevc_models
    
    logger.info("Unloading FreeVC models...")
    _freevc_models["net_g"] = None
    _freevc_models["cmodel"] = None
    _freevc_models["smodel"] = None
    _freevc_models["hps"] = None
    _freevc_models["loaded"] = False
    
    # 가비지 컬렉션 강제 실행
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.info("GPU cache cleared")
    
    logger.info("FreeVC models unloaded")

