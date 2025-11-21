"""
SCRFD GPU Face Detector
Fast and accurate GPU-based face detection using SCRFD model
"""

import os
import cv2
import numpy as np
import torch
from torch.utils.model_zoo import load_url

from ..core import FaceDetector

INSIGHTFACE_AVAILABLE = False
IMPORT_ERROR = None

try:
    import insightface
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError as e:
    INSIGHTFACE_AVAILABLE = False
    IMPORT_ERROR = str(e)
except Exception as e:
    # 다른 예외도 잡기 (예: CUDA 관련 에러)
    INSIGHTFACE_AVAILABLE = False
    IMPORT_ERROR = f"{type(e).__name__}: {str(e)}"


class SCRFDDetector(FaceDetector):
    """
    SCRFD GPU Face Detector
    
    SCRFD (Sample and Computation Redistribution for Efficient Face Detection)
    is a fast and accurate face detection model optimized for GPU inference.
    """
    
    def __init__(self, device, path_to_detector=None, verbose=False):
        super(SCRFDDetector, self).__init__(device, verbose)
        
        # Import 체크를 다시 시도 (런타임에 다시 확인)
        try:
            import insightface
            from insightface.app import FaceAnalysis
        except ImportError as e:
            error_msg = (
                "insightface is required for SCRFD detector. "
                "Install with: pip install insightface"
            )
            if IMPORT_ERROR:
                error_msg += f"\nImport error: {IMPORT_ERROR}"
            if verbose:
                import sys
                print(f"Python path: {sys.path}", file=sys.stderr)
                print(f"Trying to import insightface...", file=sys.stderr)
            raise ImportError(error_msg) from e
        
        # Initialize InsightFace FaceAnalysis with SCRFD model
        # SCRFD is the default detector in InsightFace
        try:
            self.app = FaceAnalysis(
                name='buffalo_l',  # Large model (best accuracy)
                providers=['CUDAExecutionProvider'] if 'cuda' in device else ['CPUExecutionProvider']
            )
            self.app.prepare(ctx_id=0 if 'cuda' in device else -1, det_size=(640, 640))
        except Exception as e:
            if verbose:
                import sys
                print(f"Failed to initialize InsightFace: {e}", file=sys.stderr)
            raise RuntimeError(f"Failed to initialize InsightFace FaceAnalysis: {e}") from e
        
        if self.verbose:
            print(f"SCRFD detector initialized on {device}")
    
    def detect_from_image(self, tensor_or_path):
        """Detect faces from a single image"""
        image = self.tensor_or_path_to_ndarray(tensor_or_path, rgb=False)
        
        # InsightFace expects RGB, but we have BGR from OpenCV
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Run detection
        faces = self.app.get(image_rgb)
        
        if len(faces) == 0:
            return []
        
        # Convert to format: [x1, y1, x2, y2, confidence]
        bboxlist = []
        for face in faces:
            bbox = face.bbox  # [x1, y1, x2, y2]
            confidence = face.det_score
            bboxlist.append([bbox[0], bbox[1], bbox[2], bbox[3], confidence])
        
        # Filter by confidence threshold
        bboxlist = [x for x in bboxlist if x[-1] > 0.5]
        
        return bboxlist
    
    def detect_from_batch(self, images):
        """Detect faces from a batch of images (GPU optimized)"""
        bboxlists = []
        
        for image in images:
            # Convert to RGB if needed
            if isinstance(image, np.ndarray):
                if len(image.shape) == 3 and image.shape[2] == 3:
                    # Assume BGR from OpenCV, convert to RGB
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                else:
                    image_rgb = image
            else:
                image_rgb = self.tensor_or_path_to_ndarray(image, rgb=True)
            
            # Run detection
            faces = self.app.get(image_rgb)
            
            if len(faces) == 0:
                bboxlists.append([])
                continue
            
            # Convert to format: [x1, y1, x2, y2, confidence]
            bboxlist = []
            for face in faces:
                bbox = face.bbox  # [x1, y1, x2, y2]
                confidence = face.det_score
                bboxlist.append([bbox[0], bbox[1], bbox[2], bbox[3], confidence])
            
            # Filter by confidence threshold
            bboxlist = [x for x in bboxlist if x[-1] > 0.5]
            bboxlists.append(bboxlist)
        
        return bboxlists
    
    @property
    def reference_scale(self):
        """Reference scale for face alignment (SCRFD specific)"""
        return 195
    
    @property
    def reference_x_shift(self):
        """Reference x shift for face alignment"""
        return 0
    
    @property
    def reference_y_shift(self):
        """Reference y shift for face alignment"""
        return 0

