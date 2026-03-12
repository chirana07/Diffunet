"""
=============================================================
  SwinLLIE Backend for Kaggle + ngrok
  Paste ALL cells into a Kaggle Notebook (GPU T4 x2)
  Run cells top to bottom.
=============================================================

CELL 1 — Install dependencies
--------------------------------------------------------------
!pip install -q fastapi uvicorn python-multipart pyngrok pillow timm einops
!pip install -q scikit-image   # for real PSNR/SSIM

--------------------------------------------------------------
CELL 2 — Clone your repo & load model
--------------------------------------------------------------
import os, sys, subprocess

# ---- Clone SwinLLIE from your GitHub (adjust URL) ----------
REPO_URL = "https://github.com/kavindamihiran/SwinLLIE.git"
BRANCH   = "final"

if not os.path.exists("/kaggle/working/SwinLLIE"):
    subprocess.run(["git", "clone", "-b", BRANCH, REPO_URL,
                    "/kaggle/working/SwinLLIE"], check=True)

sys.path.insert(0, "/kaggle/working/SwinLLIE")
os.chdir("/kaggle/working/SwinLLIE")

--------------------------------------------------------------
CELL 3 — Load model
--------------------------------------------------------------
import torch
from swinllie import SwinLLIE

CHECKPOINT_PATH = "./experiments/test_run/checkpoints/best.pth"
WINDOW_SIZE     = 8
DEVICE          = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Using device: {DEVICE}")

model = SwinLLIE()
ckpt  = torch.load(CHECKPOINT_PATH, map_location=DEVICE, weights_only=False)
model.load_state_dict(ckpt["model_state_dict"], strict=False)
model = model.to(DEVICE)
model.eval()
print("✅ Model loaded!")

--------------------------------------------------------------
CELL 4 — FastAPI app + inference helpers
--------------------------------------------------------------
import io, uuid, time, base64
import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr_fn
from skimage.metrics import structural_similarity as ssim_fn

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

# -------------------------------------------------------
# Inference helpers
# -------------------------------------------------------
def pad_to_multiple(x, unit=32):
    H, W = x.shape[2], x.shape[3]
    pad_h = (unit - H % unit) % unit
    pad_w = (unit - W % unit) % unit
    return torch.nn.functional.pad(x, (0, pad_w, 0, pad_h), mode="reflect"), H, W

def tensor_to_pil(t):
    arr = t.squeeze(0).permute(1, 2, 0).cpu().numpy()
    arr = np.clip(arr * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def pil_to_tensor(img):
    arr = np.array(img).astype(np.float32) / 255.0
    return torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)

def enhance_image_bytes(img_bytes: bytes) -> tuple[bytes, float, float, float]:
    """Run SwinLLIE on raw image bytes. Returns (enhanced_bytes, psnr, ssim, time)."""
    start = time.time()

    orig = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    x    = pil_to_tensor(orig).to(DEVICE)

    padded, H, W = pad_to_multiple(x, unit=WINDOW_SIZE * 4)

    with torch.no_grad():
        out = model(padded)

    out = out[:, :, :H, :W]
    enhanced = tensor_to_pil(out)

    # Calculate real PSNR / SSIM against the original
    orig_arr     = np.array(orig)
    enhanced_arr = np.array(enhanced.resize(orig.size))

    p = round(float(psnr_fn(orig_arr, enhanced_arr, data_range=255)), 2)
    s = round(float(ssim_fn(orig_arr, enhanced_arr,
                             channel_axis=2, data_range=255)), 4)

    buf = io.BytesIO()
    enhanced.save(buf, format="PNG")
    elapsed = round(time.time() - start, 2)

    return buf.getvalue(), p, s, elapsed

# -------------------------------------------------------
# FastAPI
# -------------------------------------------------------
app = FastAPI(title="SwinLLIE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Vercel / localhost both work
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store  {session_id: original_bytes}
SESSIONS: dict[str, bytes] = {}

class QualityRequest(BaseModel):
    session_id: str

@app.get("/")
def root():
    return {"status": "ok", "gpu": DEVICE}

@app.get("/health")
def health():
    return {"status": "ok", "gpu": DEVICE,
            "cuda_name": torch.cuda.get_device_name(0) if DEVICE == "cuda" else "N/A"}

@app.post("/api/enhance/fast")
async def enhance_fast(image: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/jpg", "image/png"}
    if image.content_type not in allowed:
        raise HTTPException(400, "Only JPG / PNG allowed.")

    contents = await image.read()
    if len(contents) > 10 * 1024 * 1024:   # 10 MB limit on Kaggle
        raise HTTPException(400, "File too large (max 10 MB).")

    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = contents          # store for quality mode

    try:
        enhanced_bytes, p, s, elapsed = enhance_image_bytes(contents)
    except Exception as e:
        raise HTTPException(500, str(e))

    orig_b64     = base64.b64encode(contents).decode()
    enhanced_b64 = base64.b64encode(enhanced_bytes).decode()

    return {
        "success":         True,
        "session_id":      session_id,
        "original_url":    f"data:image/png;base64,{orig_b64}",
        "image_url":       f"data:image/png;base64,{enhanced_b64}",
        "psnr":            p,
        "ssim":            s,
        "mode":            "fast",
        "processing_time": elapsed,
    }

@app.post("/api/enhance/quality")
async def enhance_quality(req: QualityRequest):
    contents = SESSIONS.get(req.session_id)
    if contents is None:
        raise HTTPException(404, "Session not found. Please upload image again.")

    try:
        enhanced_bytes, p, s, elapsed = enhance_image_bytes(contents)
    except Exception as e:
        raise HTTPException(500, str(e))

    enhanced_b64 = base64.b64encode(enhanced_bytes).decode()

    return {
        "success":         True,
        "session_id":      req.session_id,
        "image_url":       f"data:image/png;base64,{enhanced_b64}",
        "psnr":            p,
        "ssim":            s,
        "mode":            "quality",
        "processing_time": elapsed,
    }

--------------------------------------------------------------
CELL 5 — Start ngrok tunnel + run server (foreground, live logs)
--------------------------------------------------------------
import nest_asyncio
import uvicorn
from pyngrok import ngrok

nest_asyncio.apply()   # allow asyncio.run() inside Kaggle's existing event loop

# ⚠️  Paste your ngrok auth token from https://dashboard.ngrok.com
NGROK_AUTH_TOKEN = "PASTE_YOUR_NGROK_AUTH_TOKEN_HERE"
ngrok.set_auth_token(NGROK_AUTH_TOKEN)

# Kill any existing tunnels then open a fresh one
ngrok.kill()
public_url = ngrok.connect(8000)

print("=" * 60)
print(f"  🚀 Backend URL: {public_url}")
print("  Copy this URL into .env.local as NEXT_PUBLIC_BACKEND_URL")
print("=" * 60)
print("  Uvicorn starting — live request logs will appear below:")
print("  (Stop this cell to shut down the server)")
print("=" * 60)

# await server.serve() directly — works inside Kaggle's running event loop
config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
server = uvicorn.Server(config)
await server.serve()
