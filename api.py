import io
import os
import sys
import time
import uuid
import base64
from typing import Optional

import numpy as np
import torch
import torchvision.transforms.functional as TF
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

sys.path.append("src")

from config import Config
from model import PureDiffusionUNet
from diffusion import DiffusionEngine

# --------------------------------------------------
# App setup
# --------------------------------------------------
app = FastAPI(title="LuminaDiff API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Config / model init
# --------------------------------------------------
conf = Config()
device = conf.DEVICE

print(f"Using device: {device}")

model = PureDiffusionUNet().to(device)
diff = DiffusionEngine()

checkpoint_path = "checkpoints/latest.pth"
print(f"Loading checkpoint from: {checkpoint_path}")

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

model.eval()
print("Model loaded successfully")

# --------------------------------------------------
# Session storage
# --------------------------------------------------
SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)


# --------------------------------------------------
# Request / response models
# --------------------------------------------------
class QualityEnhanceRequest(BaseModel):
    session_id: str


# --------------------------------------------------
# Helper functions
# --------------------------------------------------
def pil_to_data_url(img: Image.Image, fmt: str = "PNG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def bytes_to_pil(img_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(img_bytes)).convert("RGB")


def save_original_for_session(img: Image.Image, session_id: str) -> str:
    path = os.path.join(SESSION_DIR, f"{session_id}_original.png")
    img.save(path)
    return path


def load_original_for_session(session_id: str) -> Image.Image:
    path = os.path.join(SESSION_DIR, f"{session_id}_original.png")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Original image not found for session_id={session_id}")
    return Image.open(path).convert("RGB")


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


def compute_metrics(reference_img: Image.Image, test_img: Image.Image) -> tuple[float, float]:
    """
    Computes PSNR and SSIM between two same-size RGB images.
    Note:
    These metrics compare enhanced output to the original dark input,
    not to a true ground-truth clean image.
    """
    if test_img.size != reference_img.size:
        test_img = test_img.resize(reference_img.size, Image.Resampling.LANCZOS)

    ref_np = np.array(reference_img.convert("RGB"), dtype=np.uint8)
    test_np = np.array(test_img.convert("RGB"), dtype=np.uint8)

    psnr = peak_signal_noise_ratio(ref_np, test_np, data_range=255)
    ssim = structural_similarity(ref_np, test_np, channel_axis=2, data_range=255)

    return round(float(psnr), 4), round(float(ssim), 4)


# --------------------------------------------------
# Health routes
# --------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "LuminaDiff server running",
        "gpu": device,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "gpu": device,
        "img_size": conf.IMG_SIZE,
        "timesteps": conf.TIMESTEPS,
    }


# --------------------------------------------------
# API routes
# --------------------------------------------------
@app.post("/api/enhance/fast")
async def enhance_fast(image: UploadFile = File(...)):
    """
    Stage 1:
    - accepts uploaded image
    - saves original by session_id
    - runs diffusion once
    - returns original_url + image_url + metrics + session_id
    """
    allowed = {"image/jpeg", "image/jpg", "image/png"}

    if image.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPG / PNG allowed.")

    contents = await image.read()

    if not contents:
        raise HTTPException(status_code=400, detail="Empty file.")

    # Optional file size guard: 10 MB
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    try:
        session_id = str(uuid.uuid4())

        original_img = bytes_to_pil(contents)
        save_original_for_session(original_img, session_id)

        enhanced_img, elapsed = run_diffusion_enhancement(original_img)
        psnr, ssim = compute_metrics(original_img, enhanced_img)

        return {
            "success": True,
            "session_id": session_id,
            "original_url": pil_to_data_url(original_img),
            "image_url": pil_to_data_url(enhanced_img),
            "psnr": psnr,
            "ssim": ssim,
            "mode": "fast",
            "processing_time": elapsed,
        }

    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        raise HTTPException(status_code=500, detail="CUDA out of memory.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/enhance/quality")
async def enhance_quality(request: QualityEnhanceRequest):
    """
    Stage 2:
    - accepts session_id
    - loads the previously uploaded original image
    - runs diffusion again
    - returns enhanced image + updated metrics
    """
    try:
        original_img = load_original_for_session(request.session_id)

        enhanced_img, elapsed = run_diffusion_enhancement(original_img)
        psnr, ssim = compute_metrics(original_img, enhanced_img)

        return {
            "success": True,
            "session_id": request.session_id,
            "image_url": pil_to_data_url(enhanced_img),
            "psnr": psnr,
            "ssim": ssim,
            "mode": "quality",
            "processing_time": elapsed,
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Original image not found. Please upload again.",
        )
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        raise HTTPException(status_code=500, detail="CUDA out of memory.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Optional compatibility endpoint
@app.post("/api/enhance")
async def enhance_single(image: UploadFile = File(...)):
    """
    Optional backward-compatible single endpoint.
    Behaves like /api/enhance/fast.
    """
    return await enhance_fast(image)
