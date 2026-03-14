import io
import os
import sys
import time
import uuid
import base64

import torch
import numpy as np
import torchvision.transforms.functional as TF

from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

sys.path.append("src")

from config import Config
from model import PureDiffusionUNet
from diffusion import DiffusionEngine

app = FastAPI(title="LuminaDiff API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conf = Config()
device = conf.DEVICE

print(f"Using device: {device}")

# ---------------------------
# Model init
# ---------------------------
model = PureDiffusionUNet().to(device)
diff = DiffusionEngine()

checkpoint_path = "checkpoints/latest.pth"
print(f"Loading checkpoint from: {checkpoint_path}")

try:
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)

    if isinstance(checkpoint, dict) and "ema" in checkpoint:
        model.load_state_dict(checkpoint["ema"])
        print("Loaded EMA weights")
    elif isinstance(checkpoint, dict) and "model" in checkpoint:
        model.load_state_dict(checkpoint["model"])
        print("Loaded model weights")
    else:
        model.load_state_dict(checkpoint)
        print("Loaded raw state dict")

    print("✅ Model loaded successfully!")

except Exception as e:
    print(f"Failed to load checkpoint: {e}")
    raise

model.eval()

# Optional local storage for uploaded originals by session_id
SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)


# ---------------------------
# Helpers
# ---------------------------
def pil_to_np_rgb(img: Image.Image) -> np.ndarray:
    """Convert PIL RGB image to uint8 numpy array."""
    return np.array(img.convert("RGB"), dtype=np.uint8)


def compute_metrics(original_img: Image.Image, enhanced_img: Image.Image) -> tuple[float, float]:
    """
    Compute PSNR and SSIM between original input and enhanced output.
    Note: this is NOT ground-truth evaluation, only input-vs-output comparison.
    """
    orig_np = pil_to_np_rgb(original_img)
    enh_np = pil_to_np_rgb(enhanced_img)

    # Ensure same size
    if orig_np.shape != enh_np.shape:
        enhanced_img = enhanced_img.resize(original_img.size, Image.Resampling.LANCZOS)
        enh_np = pil_to_np_rgb(enhanced_img)

    psnr = float(peak_signal_noise_ratio(orig_np, enh_np, data_range=255))
    ssim = float(structural_similarity(orig_np, enh_np, channel_axis=2, data_range=255))

    return round(psnr, 4), round(ssim, 4)


def run_diffusion_enhancement(input_pil: Image.Image) -> tuple[Image.Image, float]:
    """
    Runs the diffusion model and returns:
    - enhanced PIL image
    - elapsed time in seconds
    """
    start = time.time()

    original_size = input_pil.size
    low_resized = TF.resize(input_pil, (conf.IMG_SIZE, conf.IMG_SIZE))
    low_tensor = (TF.to_tensor(low_resized) - 0.5) * 2.0
    low_tensor = low_tensor.unsqueeze(0).to(device)

    with torch.inference_mode():
        gen_tensor = diff.sample(model, low_tensor)

    gen_tensor = (gen_tensor + 1.0) / 2.0
    gen_tensor = torch.clamp(gen_tensor, 0.0, 1.0)

    gen_img = TF.to_pil_image(gen_tensor.squeeze(0).cpu())
    gen_img = gen_img.resize(original_size, Image.Resampling.LANCZOS)

    elapsed = round(time.time() - start, 2)
    return gen_img, elapsed


def pil_to_data_url(img: Image.Image, fmt: str = "PNG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def bytes_to_pil(img_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(img_bytes)).convert("RGB")


# ---------------------------
# Routes
# ---------------------------
@app.get("/")
def root():
    return {"status": "ok", "gpu": device}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "gpu": device,
        "img_size": conf.IMG_SIZE,
        "timesteps": conf.TIMESTEPS,
    }


@app.post("/api/enhance/quality")
async def enhance_quality(image: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/jpg", "image/png"}
    if image.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPG / PNG allowed.")

    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        session_id = str(uuid.uuid4())

        original_img = bytes_to_pil(contents)

        # Optional: save original by session_id for debugging/future reuse
        original_path = os.path.join(SESSION_DIR, f"{session_id}_original.png")
        original_img.save(original_path)

        enhanced_img, elapsed = run_diffusion_enhancement(original_img)

        psnr, ssim = compute_metrics(original_img, enhanced_img)

        return {
            "success": True,
            "session_id": session_id,
            "original_url": pil_to_data_url(original_img),
            "image_url": pil_to_data_url(enhanced_img),
            "psnr": psnr,
            "ssim": ssim,
            "mode": "quality",
            "processing_time": elapsed,
        }

    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        raise HTTPException(status_code=500, detail="CUDA out of memory.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Optional compatibility endpoint:
# lets your current frontend keep calling /api/enhance/fast
# while still using diffusion underneath
@app.post("/api/enhance/fast")
async def enhance_fast(image: UploadFile = File(...)):
    result = await enhance_quality(image)
    if isinstance(result, dict):
        result["mode"] = "fast"
    return result


# Optional backward-compatible single endpoint
@app.post("/api/enhance")
async def enhance_single(image: UploadFile = File(...)):
    return await enhance_quality(image)
