import io
import time
import base64
import torch
import torchvision.transforms.functional as TF
from PIL import Image

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import sys
sys.path.append('src')

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

# Initialize Model and Diffusion Engine
model = PureDiffusionUNet().to(device)
diff = DiffusionEngine()

checkpoint_path = "checkpoints/latest.pth"
print(f"Loading checkpoint from: {checkpoint_path}")
try:
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    if 'ema' in checkpoint:
        model.load_state_dict(checkpoint['ema'])
    elif 'model' in checkpoint:
        model.load_state_dict(checkpoint['model'])
    else:
        model.load_state_dict(checkpoint)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"Failed to load checkpoint: {e}")

model.eval()

def enhance_image_bytes(img_bytes: bytes):
    start = time.time()
    low = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    original_size = low.size
    
    low_resized = TF.resize(low, (conf.IMG_SIZE, conf.IMG_SIZE))
    low_tensor = (TF.to_tensor(low_resized) - 0.5) * 2.0
    low_tensor = low_tensor.unsqueeze(0).to(device)
    
    with torch.no_grad():
        gen_tensor = diff.sample(model, low_tensor)
        
    gen_tensor = (gen_tensor + 1.0) / 2.0
    gen_tensor = torch.clamp(gen_tensor, 0.0, 1.0)
    gen_img = TF.to_pil_image(gen_tensor.squeeze(0).cpu())
    gen_img = gen_img.resize(original_size, Image.Resampling.LANCZOS)
    
    buf = io.BytesIO()
    gen_img.save(buf, format="PNG")
    elapsed = round(time.time() - start, 2)
    
    return buf.getvalue(), elapsed

@app.get("/")
def root():
    return {"status": "ok", "gpu": device}

@app.post("/api/enhance")
async def enhance_image(image: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/jpg", "image/png"}
    if image.content_type not in allowed:
        raise HTTPException(400, "Only JPG / PNG allowed.")
        
    contents = await image.read()
    
    try:
        enhanced_bytes, elapsed = enhance_image_bytes(contents)
    except Exception as e:
        raise HTTPException(500, str(e))
        
    orig_b64 = base64.b64encode(contents).decode()
    enhanced_b64 = base64.b64encode(enhanced_bytes).decode()
    
    return {
        "success": True,
        "original_url": f"data:image/png;base64,{orig_b64}",
        "image_url": f"data:image/png;base64,{enhanced_b64}",
        "processing_time": elapsed,
    }

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
