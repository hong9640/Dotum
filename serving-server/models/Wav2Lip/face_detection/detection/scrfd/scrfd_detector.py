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
    
    def __init__(self, device, path_to_detector=None, verbose=True):
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
        """Detect faces from a batch of images (True GPU batch processing)"""
        if len(images) == 0:
            return []
        
        # Convert all images to RGB in batch
        images_rgb = []
        for image in images:
            if isinstance(image, np.ndarray):
                if len(image.shape) == 3 and image.shape[2] == 3:
                    # Assume BGR from OpenCV, convert to RGB
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                else:
                    image_rgb = image
            else:
                image_rgb = self.tensor_or_path_to_ndarray(image, rgb=True)
            images_rgb.append(image_rgb)
        
        bboxlists = []
        
        # Try to access InsightFace's internal detection model for batch processing
        # InsightFace structure: app.models['detection'] or app.det_model
        # 강제로 verbose 출력 (항상 로그 확인)
        print(f"[SCRFD Batch] Starting batch processing for {len(images)} images")
        print(f"[SCRFD Batch] Attempting to access detection model...")
        print(f"[SCRFD Batch] app type: {type(self.app)}")
        
        try:
            det_model = None
            det_size = (640, 640)
            
            # InsightFace의 실제 구조 확인
            app_attrs = [attr for attr in dir(self.app) if not attr.startswith('_')]
            print(f"[SCRFD Batch] app attributes: {app_attrs[:20]}...")  # 처음 20개만
            
            # InsightFace의 실제 구조: app.models는 dict가 아니라 list일 수 있음
            # 또는 app.det_model이 직접 접근 가능할 수 있음
            
            # 방법 1: app.models 확인 (dict 또는 list)
            if hasattr(self.app, 'models'):
                models_attr = self.app.models
                print(f"[SCRFD Batch] Found app.models: type={type(models_attr)}")
                
                if isinstance(models_attr, dict):
                    print(f"[SCRFD Batch] app.models keys: {list(models_attr.keys())}")
                    det_model = models_attr.get('detection', None)
                elif isinstance(models_attr, (list, tuple)) and len(models_attr) > 0:
                    # models가 list인 경우 첫 번째가 detection일 수 있음
                    print(f"[SCRFD Batch] app.models is list/tuple with {len(models_attr)} items")
                    for idx, model in enumerate(models_attr):
                        if hasattr(model, 'run') or (hasattr(model, '__class__') and 'det' in str(model.__class__).lower()):
                            print(f"[SCRFD Batch] Found potential det model at index {idx}: {type(model)}")
                            det_model = model
                            break
            
            # 방법 2: app.det_model 직접 접근
            if det_model is None and hasattr(self.app, 'det_model'):
                det_model = self.app.det_model
                print(f"[SCRFD Batch] Found app.det_model: {type(det_model)}")
            
            # 방법 3: app.detector 접근
            if det_model is None and hasattr(self.app, 'detector'):
                det_model = self.app.detector
                print(f"[SCRFD Batch] Found app.detector: {type(det_model)}")
            
            # 방법 4: app.__dict__를 통한 접근
            if det_model is None and hasattr(self.app, '__dict__'):
                app_dict = self.app.__dict__
                print(f"[SCRFD Batch] app.__dict__ keys: {list(app_dict.keys())[:15]}...")
                
                # 'det'가 포함된 모든 속성 확인
                for key, value in app_dict.items():
                    if 'det' in key.lower():
                        print(f"[SCRFD Batch] Found '{key}': {type(value)}")
                        if hasattr(value, 'run') or (hasattr(value, '__class__') and 'onnx' in str(value.__class__).lower()):
                            print(f"[SCRFD Batch] '{key}' looks like ONNX model, using it")
                            det_model = value
                            break
                    
                    # 또는 'model'이 포함된 속성도 확인
                    if 'model' in key.lower() and hasattr(value, 'run'):
                        print(f"[SCRFD Batch] Found '{key}' with 'run' method: {type(value)}")
                        det_model = value
                        break
            
            if det_model is not None:
                print(f"[SCRFD Batch] ✅ Successfully found detection model: {type(det_model)}")
                
                # RetinaFace는 래퍼 클래스이므로 내부 ONNX 모델 찾기
                onnx_model = None
                if hasattr(det_model, 'session'):
                    # InsightFace의 RetinaFace는 일반적으로 session 속성에 ONNX Runtime InferenceSession을 가짐
                    onnx_model = det_model.session
                    print(f"[SCRFD Batch] Found ONNX model via .session: {type(onnx_model)}")
                elif hasattr(det_model, 'model'):
                    onnx_model = det_model.model
                    print(f"[SCRFD Batch] Found ONNX model via .model: {type(onnx_model)}")
                elif hasattr(det_model, 'onnx_model'):
                    onnx_model = det_model.onnx_model
                    print(f"[SCRFD Batch] Found ONNX model via .onnx_model: {type(onnx_model)}")
                elif hasattr(det_model, '__dict__'):
                    # RetinaFace 객체의 모든 속성 검색
                    for attr_name in ['session', 'model', 'onnx_model', 'inference_session', 'ort_session']:
                        if hasattr(det_model, attr_name):
                            attr_value = getattr(det_model, attr_name)
                            if hasattr(attr_value, 'run') or hasattr(attr_value, 'get_inputs'):
                                onnx_model = attr_value
                                print(f"[SCRFD Batch] Found ONNX model via .{attr_name}: {type(onnx_model)}")
                                break
                
                # ONNX 모델이 직접 접근 가능한 경우 (이미 ONNX Runtime InferenceSession)
                if onnx_model is None and hasattr(det_model, 'get_inputs'):
                    onnx_model = det_model
                    print(f"[SCRFD Batch] Model itself is ONNX Runtime InferenceSession")
                
                if onnx_model is not None:
                    det_model = onnx_model
                    # Check if it's an ONNX model
                    if hasattr(det_model, 'get_inputs'):
                        try:
                            inputs = det_model.get_inputs()
                            input_names = [inp.name for inp in inputs]
                            print(f"[SCRFD Batch] ONNX model inputs: {input_names}")
                            if len(inputs) > 0:
                                input_shape = inputs[0].shape if hasattr(inputs[0], 'shape') else 'dynamic'
                                print(f"[SCRFD Batch] Input shape: {input_shape}")
                        except Exception as e:
                            print(f"[SCRFD Batch] Error getting inputs: {e}")
                    else:
                        print(f"[SCRFD Batch] ⚠️ ONNX model doesn't have 'get_inputs' method")
                        det_model = None
                else:
                    print(f"[SCRFD Batch] ⚠️ Cannot find ONNX Runtime InferenceSession in RetinaFace object")
                    print(f"[SCRFD Batch] RetinaFace attributes: {[attr for attr in dir(det_model) if not attr.startswith('_')][:20]}")
                    det_model = None
                
                # Get detection size from app if available
                if hasattr(self.app, 'det_size'):
                    det_size = self.app.det_size
                elif hasattr(self.app, 'input_size'):
                    det_size = self.app.input_size
                else:
                    det_size = (640, 640)  # Default
                
                # Prepare batch input: (batch_size, 3, height, width)
                batch_inputs = []
                original_shapes = []
                
                for img_rgb in images_rgb:
                    orig_h, orig_w = img_rgb.shape[:2]
                    original_shapes.append((orig_h, orig_w))
                    
                    # Resize to detection size
                    img_resized = cv2.resize(img_rgb, det_size)
                    
                    # Convert to (3, H, W) and normalize
                    # InsightFace normalization: (img - 127.5) / 128.0
                    img_tensor = img_resized.transpose(2, 0, 1).astype(np.float32)
                    img_tensor = (img_tensor - 127.5) / 128.0
                    batch_inputs.append(img_tensor)
                
                # Stack into batch: (batch_size, 3, 640, 640)
                batch_tensor = np.stack(batch_inputs, axis=0)
                
                # Get input name from ONNX model
                try:
                    input_name = None
                    if hasattr(det_model, 'get_inputs'):
                        inputs = det_model.get_inputs()
                        if len(inputs) > 0:
                            input_name = inputs[0].name
                            print(f"[SCRFD Batch] Using input name: {input_name}")
                    elif hasattr(det_model, 'inputs'):
                        if len(det_model.inputs) > 0:
                            input_name = det_model.inputs[0].name
                            print(f"[SCRFD Batch] Using input name from .inputs: {input_name}")
                    
                    if input_name is None:
                        raise AttributeError("Cannot find input name from model")
                    
                    print(f"[SCRFD Batch] Batch tensor shape: {batch_tensor.shape}, dtype: {batch_tensor.dtype}")
                    print(f"[SCRFD Batch] Running batch inference...")
                    
                    # Run batch inference
                    outputs = det_model.run(None, {input_name: batch_tensor})
                    
                    print(f"[SCRFD Batch] ✅ Batch inference successful! Output count: {len(outputs)}")
                    if len(outputs) > 0:
                        print(f"[SCRFD Batch] Output[0] shape: {outputs[0].shape}")
                    if len(outputs) > 1:
                        print(f"[SCRFD Batch] Output[1] shape: {outputs[1].shape}")
                    
                    # Process outputs for each image in batch
                    # SCRFD output format varies, try to handle common formats
                    for batch_idx, (img_rgb, (orig_h, orig_w)) in enumerate(zip(images_rgb, original_shapes)):
                        bboxlist = []
                        
                        # Scale factors
                        scale_x = orig_w / det_size[0]
                        scale_y = orig_h / det_size[1]
                        
                        # Extract detections for this image
                        # Common formats:
                        # 1. [boxes, scores] - two outputs
                        # 2. [combined] - single output with boxes and scores
                        # 3. [boxes, scores, landmarks] - three outputs
                        
                        if len(outputs) >= 2:
                            # Format: [boxes, scores]
                            boxes = outputs[0][batch_idx]  # Shape: (N, 4) or (N, 5)
                            scores = outputs[1][batch_idx]  # Shape: (N,)
                            
                            # Handle different box formats
                            if boxes.shape[1] == 5:
                                # Boxes include confidence: [x1, y1, x2, y2, conf]
                                boxes_xyxy = boxes[:, :4]
                                scores = boxes[:, 4] if scores is None or scores.size == 0 else scores
                            else:
                                boxes_xyxy = boxes[:, :4]
                            
                            # Filter by confidence
                            if scores is not None and len(scores) > 0:
                                valid_mask = scores > 0.5
                                boxes_xyxy = boxes_xyxy[valid_mask]
                                scores = scores[valid_mask]
                            
                            # Scale and convert to list
                            for box, score in zip(boxes_xyxy, scores if scores is not None else [1.0] * len(boxes_xyxy)):
                                x1 = int(box[0] * scale_x)
                                y1 = int(box[1] * scale_y)
                                x2 = int(box[2] * scale_x)
                                y2 = int(box[3] * scale_y)
                                conf = float(score) if scores is not None else 1.0
                                bboxlist.append([x1, y1, x2, y2, conf])
                        else:
                            # Single output format
                            output = outputs[0][batch_idx]  # Shape: (N, 5) or (N, 6)
                            
                            if output.shape[1] >= 5:
                                boxes = output[:, :4]
                                scores = output[:, 4] if output.shape[1] > 4 else None
                                
                                if scores is not None:
                                    valid_mask = scores > 0.5
                                    boxes = boxes[valid_mask]
                                    scores = scores[valid_mask]
                                
                                for i, box in enumerate(boxes):
                                    x1 = int(box[0] * scale_x)
                                    y1 = int(box[1] * scale_y)
                                    x2 = int(box[2] * scale_x)
                                    y2 = int(box[3] * scale_y)
                                    conf = float(scores[i]) if scores is not None else 1.0
                                    bboxlist.append([x1, y1, x2, y2, conf])
                            else:
                                # No scores, just boxes
                                for box in output:
                                    x1 = int(box[0] * scale_x)
                                    y1 = int(box[1] * scale_y)
                                    x2 = int(box[2] * scale_x)
                                    y2 = int(box[3] * scale_y)
                                    bboxlist.append([x1, y1, x2, y2, 1.0])
                        
                        # Final confidence filter
                        bboxlist = [x for x in bboxlist if x[-1] > 0.5]
                        bboxlists.append(bboxlist)
                    
                    # Successfully used batch processing
                    print(f"[SCRFD Batch] ✅✅✅ Successfully processed batch of {len(images)} images using GPU batch inference!")
                    print(f"[SCRFD Batch] Performance: {len(images)} images in single batch (vs {len(images)} sequential calls)")
                    return bboxlists
                    
                except Exception as batch_e:
                    import traceback
                    print(f"[SCRFD Batch] ❌ Batch inference error: {batch_e}")
                    print(f"[SCRFD Batch] Error type: {type(batch_e).__name__}")
                    print(f"[SCRFD Batch] Traceback:")
                    traceback.print_exc()
                    print(f"[SCRFD Batch] Falling back to sequential processing")
                    # Fall through to sequential processing
            else:
                print("[SCRFD Batch] ❌ Detection model not accessible, using sequential processing")
                det_attrs = [attr for attr in dir(self.app) if not attr.startswith('_') and 'det' in attr.lower()]
                print(f"[SCRFD Batch] Available 'det' attributes: {det_attrs}")
        except Exception as e:
            import traceback
            print(f"[SCRFD Batch] ❌ Batch processing setup failed: {e}")
            print(f"[SCRFD Batch] Error type: {type(e).__name__}")
            print(f"[SCRFD Batch] Traceback:")
            traceback.print_exc()
            print(f"[SCRFD Batch] Using sequential processing")
        
        # Fallback: Sequential processing (original method)
        # This is still faster than before because we pre-converted all images
        for image_rgb in images_rgb:
            try:
                faces = self.app.get(image_rgb)
                
                if len(faces) == 0:
                    bboxlists.append([])
                    continue
                
                bboxlist = []
                for face in faces:
                    bbox = face.bbox
                    confidence = face.det_score
                    bboxlist.append([bbox[0], bbox[1], bbox[2], bbox[3], confidence])
                
                bboxlist = [x for x in bboxlist if x[-1] > 0.5]
                bboxlists.append(bboxlist)
            except Exception as img_e:
                if self.verbose:
                    print(f"Error processing image: {img_e}")
                bboxlists.append([])
        
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

