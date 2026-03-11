
import torch
import os

class Config:
    DATASET_ROOT = "./input" 
    SAVE_DIR = "./checkpoints"
    RESULT_DIR = "./results"
    
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        os.makedirs(RESULT_DIR, exist_ok=True)
    except OSError:
        pass

    IMG_SIZE = 128          
    BATCH_SIZE = 16         
    EPOCHS = 300            # TARGET: 300 Epochs
    
    LR_START = 2e-4         
    LR_MIN = 1e-6           
    WARMUP_EPOCHS = 5       
    WEIGHT_DECAY = 1e-4     
    BETAS = (0.9, 0.999)    
    GRAD_CLIP = 1.0         
    
    TIMESTEPS = 300         
    BETA_START = 0.0001
    BETA_END = 0.02
    
    CHANNELS = 32           
    CHANNEL_MULT = [1, 2, 4, 8] 
    RES_BLOCKS = 1          
    
    # --- QUALITY LOSS WEIGHTS ---
    LAMBDA_CHAR = 1.0       
    LAMBDA_SSIM = 1.0       # Stronger SSIM to kill blocks
    LAMBDA_VGG = 0.1        
    LAMBDA_TV = 0.1         # Total Variation (Smoothness)
    
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    SAMPLE_INTERVAL = 10
