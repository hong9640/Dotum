import os
import cv2
import time
import torch
import numpy as np
from torch.utils.model_zoo import load_url

from ..core import FaceDetector

from .net_s3fd import s3fd
from .bbox import *
from .detect import *

models_urls = {
    's3fd': 'https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth',
}


class SFDDetector(FaceDetector):
    def __init__(self, device, path_to_detector=os.path.join(os.path.dirname(os.path.abspath(__file__)), 's3fd.pth'), verbose=False):
        super(SFDDetector, self).__init__(device, verbose)

        # Initialise the face detector
        if not os.path.isfile(path_to_detector):
            model_weights = load_url(models_urls['s3fd'])
        else:
            model_weights = torch.load(path_to_detector)

        self.face_detector = s3fd()
        self.face_detector.load_state_dict(model_weights)
        self.face_detector.to(device)
        self.face_detector.eval()
        
        # GPU warm-up: 첫 번째 배치의 느린 속도 방지
        if 'cuda' in device:
            if verbose:
                print(f"[SFD] Performing GPU warm-up...")
            try:
                dummy_img = np.zeros((1, 256, 256, 3), dtype=np.uint8)
                _ = batch_detect(self.face_detector, dummy_img, device=device)
                if 'cuda' in device:
                    torch.cuda.synchronize()  # GPU 작업 완료 대기
                if verbose:
                    print(f"[SFD] ✅ GPU warm-up completed")
            except Exception as e:
                if verbose:
                    print(f"[SFD] ⚠️ GPU warm-up failed (non-critical): {e}")

    def detect_from_image(self, tensor_or_path):
        image = self.tensor_or_path_to_ndarray(tensor_or_path)

        bboxlist = detect(self.face_detector, image, device=self.device)
        keep = nms(bboxlist, 0.3)
        bboxlist = bboxlist[keep, :]
        bboxlist = [x for x in bboxlist if x[-1] > 0.5]

        return bboxlist

    def detect_from_batch(self, images):
        """Detect faces from a batch of images (True GPU batch processing)"""
        print(f"[SFD Batch] ========================================")
        print(f"[SFD Batch] Starting TRUE batch processing for {len(images)} images")
        print(f"[SFD Batch] Using PyTorch batch_detect (GPU optimized)")
        print(f"[SFD Batch] ========================================")
        
        batch_start = time.time()
        bboxlists = batch_detect(self.face_detector, images, device=self.device)
        batch_time = time.time() - batch_start
        
        print(f"[SFD Batch] ✅ Batch detection completed in {batch_time:.3f}s")
        print(f"[SFD Batch] Processing {len(images)} images in single batch")
        print(f"[SFD Batch] Average time per image: {batch_time/len(images):.3f}s")
        
        keeps = [nms(bboxlists[:, i, :], 0.3) for i in range(bboxlists.shape[1])]
        bboxlists = [bboxlists[keep, i, :] for i, keep in enumerate(keeps)]
        bboxlists = [[x for x in bboxlist if x[-1] > 0.5] for bboxlist in bboxlists]

        print(f"[SFD Batch] ✅✅✅ Successfully processed batch of {len(images)} images using GPU batch inference!")
        return bboxlists

    @property
    def reference_scale(self):
        return 195

    @property
    def reference_x_shift(self):
        return 0

    @property
    def reference_y_shift(self):
        return 0
