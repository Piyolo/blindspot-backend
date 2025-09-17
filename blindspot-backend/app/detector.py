from typing import List, Dict, Any, Tuple
import io, time, base64
import numpy as np
from PIL import Image, ImageDraw
from ultralytics import YOLO
import torch

class Detector:
    def __init__(self, weights: str = "yolov8n.pt", conf: float = 0.25, iou: float = 0.45):
        self.model = YOLO(weights)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(device)
        self.names = self.model.model.names if hasattr(self.model.model, "names") else self.model.names
        self.conf = conf
        self.iou = iou

    def _pil_to_nd(self, img: Image.Image) -> np.ndarray:
        return np.array(img.convert("RGB"))

    def _nd_to_pil(self, arr: np.ndarray) -> Image.Image:
        return Image.fromarray(arr)

    def infer(self, pil_image: Image.Image, return_image: bool = False, img_size: int = 640) -> Tuple[List[Dict[str, Any]], bytes | None, float]:
        """Run detection on a PIL image. Returns: detections, jpeg_bytes(optional), elapsed_ms"""
        img_nd = self._pil_to_nd(pil_image)
        t0 = time.time()
        results = self.model.predict(
            img_nd, conf=self.conf, iou=self.iou, imgsz=img_size, verbose=False
        )
        elapsed_ms = (time.time() - t0) * 1000

        dets: List[Dict[str, Any]] = []
        for r in results:
            boxes = r.boxes
            for i in range(len(boxes)):
                xyxy = boxes.xyxy[i].tolist()  # [x1,y1,x2,y2]
                cls_id = int(boxes.cls[i])
                conf = float(boxes.conf[i])
                x1, y1, x2, y2 = xyxy
                dets.append({
                    "class_id": cls_id,
                    "class_name": self.names.get(cls_id, str(cls_id)) if isinstance(self.names, dict) else self.names[cls_id],
                    "conf": round(conf, 4),
                    "box": {
                        "x": float(x1), "y": float(y1),
                        "w": float(x2 - x1), "h": float(y2 - y1)
                    }
                })

        jpeg_bytes = None
        if return_image:
            # draw boxes on copy
            canvas = pil_image.copy()
            draw = ImageDraw.Draw(canvas, "RGBA")
            for d in dets:
                x, y, w, h = d["box"]["x"], d["box"]["y"], d["box"]["w"], d["box"]["h"]
                x2, y2 = x + w, y + h
                draw.rectangle([x, y, x2, y2], outline=(66, 135, 245, 255), width=3)
                label = f'{d["class_name"]} {d["conf"]:.2f}'
                draw.text((x + 4, y + 4), label, fill=(255, 255, 255, 255))
            buf = io.BytesIO()
            canvas.save(buf, format="JPEG", quality=85)
            jpeg_bytes = buf.getvalue()

        return dets, jpeg_bytes, elapsed_ms

# Singleton instance (loaded once at startup)
detector: Detector | None = None

def get_detector() -> Detector:
    global detector
    if detector is None:
        # you can swap to weights/your_custom.pt later
        detector = Detector(weights="yolov8n.pt", conf=0.25, iou=0.45)
    return detector
