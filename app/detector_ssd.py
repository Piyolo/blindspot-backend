# app/detector_ssd.py
from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import io, time
import numpy as np
from PIL import Image, ImageDraw
import tensorflow as tf

ROOT = Path(__file__).resolve().parent

# Adjust this if your folder is named differently after extracting the .tar.gz
MODEL_DIR = ROOT / "models" / "ssd_mobilenet_v2_fpnlite_640x640_coco17_tpu-8" / "saved_model"

# COCO 2017 labels (id 1..90). Index 0 is a dummy for 1-based class ids from the model.
COCO_LABELS = [
    "??","person","bicycle","car","motorcycle","airplane","bus","train","truck","boat",
    "traffic light","fire hydrant","stop sign","parking meter","bench","bird","cat","dog",
    "horse","sheep","cow","elephant","bear","zebra","giraffe","backpack","umbrella",
    "handbag","tie","suitcase","frisbee","skis","snowboard","sports ball","kite",
    "baseball bat","baseball glove","skateboard","surfboard","tennis racket","bottle",
    "wine glass","cup","fork","knife","spoon","bowl","banana","apple","sandwich","orange",
    "broccoli","carrot","hot dog","pizza","donut","cake","chair","couch","potted plant",
    "bed","dining table","toilet","tv","laptop","mouse","remote","keyboard","cell phone",
    "microwave","oven","toaster","sink","refrigerator","book","clock","vase","scissors",
    "teddy bear","hair drier","toothbrush"
]

class SSDDetector:
    """
    Loads the **local** TF2 SavedModel (OD API export) and runs inference.
    """
    def __init__(self, score_thresh: float = 0.25):
        if not MODEL_DIR.exists():
            raise FileNotFoundError(
                f"SavedModel not found at: {MODEL_DIR}\n"
                "Make sure you extracted the tar so that this directory contains saved_model.pb and variables/."
            )
        self.model = tf.saved_model.load(str(MODEL_DIR))
        # Exported OD API models have a 'serving_default' signature
        self.infer_fn = self.model.signatures.get("serving_default")
        if self.infer_fn is None:
            raise RuntimeError("Model does not expose 'serving_default' signature.")
        self.score_thresh = score_thresh

        # Warmup
        _ = self.infer_fn(tf.zeros([1, 640, 640, 3], dtype=tf.uint8))

    @staticmethod
    def _pil_to_batched_uint8(img: Image.Image) -> tf.Tensor:
        arr = np.array(img.convert("RGB"), dtype=np.uint8)
        return tf.convert_to_tensor(arr)[tf.newaxis, ...]  # [1,H,W,3]

    def infer(
        self,
        pil_image: Image.Image,
        return_image: bool = False
    ) -> Tuple[List[Dict[str, Any]], Optional[bytes], float]:
        H, W = pil_image.height, pil_image.width
        inputs = self._pil_to_batched_uint8(pil_image)

        t0 = time.time()
        outputs = self.infer_fn(inputs)
        elapsed_ms = (time.time() - t0) * 1000.0

        # Tensors:
        # - detection_boxes: [1,100,4] (ymin,xmin,ymax,xmax) normalized
        # - detection_scores: [1,100]
        # - detection_classes: [1,100] 1-based int ids
        boxes   = outputs["detection_boxes"][0].numpy()
        scores  = outputs["detection_scores"][0].numpy()
        classes = outputs["detection_classes"][0].numpy().astype(int)
        num     = int(outputs.get("num_detections", tf.shape(scores)[-1]).numpy() if "num_detections" in outputs else scores.shape[0])

        dets: List[Dict[str, Any]] = []
        for i in range(num):
            conf = float(scores[i])
            if conf < self.score_thresh:
                continue
            cls_id = int(classes[i])  # 1..90
            name = COCO_LABELS[cls_id] if 0 <= cls_id < len(COCO_LABELS) else str(cls_id)

            ymin, xmin, ymax, xmax = boxes[i].tolist()
            x1, y1 = xmin * W, ymin * H
            x2, y2 = xmax * W, ymax * H
            dets.append({
                "class_id": cls_id,
                "class_name": name,
                "conf": round(conf, 4),
                "box": {"x": float(x1), "y": float(y1), "w": float(x2 - x1), "h": float(y2 - y1)}
            })

        jpeg_bytes = None
        if return_image:
            canvas = pil_image.copy()
            draw = ImageDraw.Draw(canvas, "RGBA")
            for d in dets:
                x, y, w, h = d["box"]["x"], d["box"]["y"], d["box"]["w"], d["box"]["h"]
                x2, y2 = x + w, y + h
                draw.rectangle([x, y, x2, y2], outline=(66, 135, 245, 255), width=3)
                draw.text((x + 4, max(0, y - 16)), f'{d["class_name"]} {d["conf"]:.2f}', fill=(255,255,255,255))
            buf = io.BytesIO()
            canvas.save(buf, "JPEG", quality=85)
            jpeg_bytes = buf.getvalue()

        return dets, jpeg_bytes, elapsed_ms

# Singleton
_detector: Optional[SSDDetector] = None
def get_detector() -> SSDDetector:
    global _detector
    if _detector is None:
        _detector = SSDDetector(score_thresh=0.25)
    return _detector
