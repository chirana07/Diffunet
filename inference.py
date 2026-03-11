import os
import glob
import torch
import torchvision.transforms.functional as TF
from PIL import Image
from tqdm import tqdm

import sys
sys.path.append('src')

from config import Config
from model import PureDiffusionUNet
from diffusion import DiffusionEngine

def main():
    conf = Config()
    
    # Paths override for local execution
    test_samples_dir = "test_samples"
    results_dir = "results"
    checkpoint_path = "checkpoints/latest.pth"
    
    os.makedirs(results_dir, exist_ok=True)
    
    device = conf.DEVICE
    print(f"Using device: {device}")
    
    # Initialize Model and Diffusion Engine
    model = PureDiffusionUNet().to(device)
    diff = DiffusionEngine()
    
    # Load Weights
    print(f"Loading checkpoint from: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    if 'ema' in checkpoint:
        print("Loading EMA weights for evaluation...")
        model.load_state_dict(checkpoint['ema'])
    elif 'model' in checkpoint:
        print("Loading standard model weights...")
        model.load_state_dict(checkpoint['model'])
    else:
        print("Loading plain weights...")
        model.load_state_dict(checkpoint)
        
    model.eval()
    
    # Gather test images
    image_paths = sorted(glob.glob(os.path.join(test_samples_dir, "*.png")) + 
                         glob.glob(os.path.join(test_samples_dir, "*.jpg")) + 
                         glob.glob(os.path.join(test_samples_dir, "*.jpeg")))
    
    if not image_paths:
        print(f"No images found in {test_samples_dir}.")
        return
        
    print(f"Found {len(image_paths)} images. Starting inference...")
    
    for img_path in tqdm(image_paths):
        basename = os.path.basename(img_path)
        
        # Load and preprocess
        low = Image.open(img_path).convert('RGB')
        
        # Store original size to resize back after inference
        original_size = low.size
        
        low_resized = TF.resize(low, (conf.IMG_SIZE, conf.IMG_SIZE))
        
        # To tensor and normalize to [-1, 1]
        low_tensor = (TF.to_tensor(low_resized) - 0.5) * 2.0
        low_tensor = low_tensor.unsqueeze(0).to(device) # Add batch dimension
        
        # Run diffusion sampling
        with torch.no_grad():
            gen_tensor = diff.sample(model, low_tensor)
            
        # Postprocess: denormalize from [-1, 1] to [0, 1]
        gen_tensor = (gen_tensor + 1.0) / 2.0
        gen_tensor = torch.clamp(gen_tensor, 0.0, 1.0)
        
        # Squeeze batch dim and convert to PIL
        gen_img = TF.to_pil_image(gen_tensor.squeeze(0).cpu())
        
        # Resize back to original dimensions for better comparison
        # (Though model output is conf.IMG_SIZE x conf.IMG_SIZE, resizing it up helps viewing)
        gen_img = gen_img.resize(original_size, Image.Resampling.LANCZOS)
        
        # Save output
        out_path = os.path.join(results_dir, f"enhanced_{basename}")
        gen_img.save(out_path)
        
    print(f"Inference complete! Results saved in {results_dir}.")

if __name__ == "__main__":
    main()
