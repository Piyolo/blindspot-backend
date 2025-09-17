from PIL import Image
import io, time

def run_detection(image_bytes: bytes, mode: str):
    t0 = time.time()
    im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return {
        "boxes": [{"xyxy":[0.1,0.2,0.6,0.8], "cls":"person", "conf":0.87}],
        "latency_ms": int((time.time()-t0)*1000),
        "mode": mode,
        "im_w": im.width, "im_h": im.height
    }
