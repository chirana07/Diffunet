
import torch
from config import Config
from tqdm import tqdm

class DiffusionEngine:
    def __init__(self):
        self.conf = Config()
        self.device = self.conf.DEVICE
        self.steps = self.conf.TIMESTEPS
        self.betas = torch.linspace(self.conf.BETA_START, self.conf.BETA_END, self.steps).to(self.device)
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = torch.cumprod(self.alphas, dim=0)
        self.alphas_cumprod_prev = torch.cat([torch.tensor([1.0]).to(self.device), self.alphas_cumprod[:-1]])
        self.posterior_mean_coef1 = (self.betas * torch.sqrt(self.alphas_cumprod_prev) / (1.0 - self.alphas_cumprod))
        self.posterior_mean_coef2 = ((1.0 - self.alphas_cumprod_prev) * torch.sqrt(self.alphas) / (1.0 - self.alphas_cumprod))
        self.posterior_variance = (self.betas * (1.0 - self.alphas_cumprod_prev) / (1.0 - self.alphas_cumprod))
        self.sqrt_alphas_cumprod = torch.sqrt(self.alphas_cumprod)
        self.sqrt_one_minus_alphas_cumprod = torch.sqrt(1.0 - self.alphas_cumprod)

    def q_sample(self, x_start, t, noise=None):
        if noise is None: noise = torch.randn_like(x_start)
        s1 = self.sqrt_alphas_cumprod[t][:, None, None, None]
        s2 = self.sqrt_one_minus_alphas_cumprod[t][:, None, None, None]
        return s1 * x_start + s2 * noise, noise

    @torch.no_grad()
    def sample(self, model, low_light):
        model.eval()
        b = low_light.shape[0]
        img = torch.randn_like(low_light)
        for i in reversed(range(0, self.steps)):
            t = torch.full((b,), i, device=self.device, dtype=torch.long)
            pred_x0 = model(img, t, low_light)
            pred_x0 = torch.clamp(pred_x0, -1, 1)
            posterior_mean = (self.posterior_mean_coef1[t][:, None, None, None] * pred_x0 + self.posterior_mean_coef2[t][:, None, None, None] * img)
            if i > 0:
                noise = torch.randn_like(img)
                var = self.posterior_variance[t][:, None, None, None]
                img = posterior_mean + torch.sqrt(var) * noise
            else:
                img = posterior_mean
        return torch.clamp(img, -1, 1)
