
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR
from copy import deepcopy
from tqdm import tqdm
import os
import glob
from config import Config
from dataset import LOLDataset
from model import PureDiffusionUNet
from diffusion import DiffusionEngine
from modules import VGGPerceptualLoss, SSIMLoss, CharbonnierLoss, TVLoss

class EMA:
    def __init__(self, model, decay=0.999):
        self.decay = decay
        self.shadow = deepcopy(model.state_dict())
    def update(self, model):
        with torch.no_grad():
            for name, param in model.named_parameters():
                if param.requires_grad:
                    self.shadow[name] = (1.0 - self.decay) * param.data + self.decay * self.shadow[name]

def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def train():
    conf = Config()
    train_loader = DataLoader(LOLDataset('train'), batch_size=conf.BATCH_SIZE, shuffle=True, num_workers=2, pin_memory=True)
    
    model = PureDiffusionUNet().to(conf.DEVICE)
    diff = DiffusionEngine()
    ema = EMA(model)
    
    optimizer = optim.AdamW(model.parameters(), lr=conf.LR_START, betas=conf.BETAS, weight_decay=conf.WEIGHT_DECAY)
    
    scheduler1 = LinearLR(optimizer, start_factor=0.01, end_factor=1.0, total_iters=conf.WARMUP_EPOCHS)
    scheduler2 = CosineAnnealingLR(optimizer, T_max=conf.EPOCHS - conf.WARMUP_EPOCHS, eta_min=conf.LR_MIN)
    scheduler = SequentialLR(optimizer, schedulers=[scheduler1, scheduler2], milestones=[conf.WARMUP_EPOCHS])
    
    # LOSSES
    crit_char = CharbonnierLoss().to(conf.DEVICE)
    crit_ssim = SSIMLoss().to(conf.DEVICE)
    crit_vgg = VGGPerceptualLoss().to(conf.DEVICE)
    crit_tv = TVLoss().to(conf.DEVICE)

    print(f"🧩 Parameters: {count_parameters(model):,} (Quality Architecture)")
    print(f"🚀 Training... (Target: 300 Epochs)")

    start_epoch = 0
    # No Resume Logic - We want a fresh start for the new architecture

    for epoch in range(start_epoch, conf.EPOCHS):
        model.train()
        pbar = tqdm(train_loader)
        
        for low, high in pbar:
            low, high = low.to(conf.DEVICE), high.to(conf.DEVICE)
            t = torch.randint(0, conf.TIMESTEPS, (low.size(0),), device=conf.DEVICE)
            x_noisy, noise = diff.q_sample(high, t)
            
            # Forward
            pred_x0 = model(x_noisy, t, low)
            
            # Weighted Losses
            loss_char = crit_char(pred_x0, high) * conf.LAMBDA_CHAR
            loss_ssim = crit_ssim(pred_x0, high) * conf.LAMBDA_SSIM
            loss_vgg = crit_vgg(pred_x0, high) * conf.LAMBDA_VGG
            loss_tv = crit_tv(pred_x0) * conf.LAMBDA_TV
            
            loss = loss_char + loss_ssim + loss_vgg + loss_tv
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), conf.GRAD_CLIP)
            optimizer.step()
            ema.update(model)
            
            pbar.set_description(f"Ep {epoch} | L: {loss.item():.3f} SSIM: {loss_ssim.item():.3f}")
        
        scheduler.step()
        
        if epoch % 5 == 0:
            torch.save({
                'epoch': epoch,
                'model': model.state_dict(),
                'optimizer': optimizer.state_dict(),
                'ema': ema.shadow
            }, os.path.join(conf.SAVE_DIR, "latest.pth"))

if __name__ == "__main__":
    train()
