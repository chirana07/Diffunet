
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import math

def init_weights(m):
    if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
        nn.init.xavier_uniform_(m.weight)
        if m.bias is not None: nn.init.zeros_(m.bias)

class Swish(nn.Module):
    def forward(self, x): return x * torch.sigmoid(x)

def get_timestep_embedding(timesteps, embedding_dim):
    half_dim = embedding_dim // 2
    emb = math.log(10000) / (half_dim - 1)
    emb = torch.exp(torch.arange(half_dim, dtype=torch.float32, device=timesteps.device) * -emb)
    emb = timesteps[:, None].float() * emb[None, :]
    emb = torch.cat([torch.sin(emb), torch.cos(emb)], dim=1)
    if embedding_dim % 2 == 1: emb = F.pad(emb, (0, 1))
    return emb

# --- ARCHITECTURE FIX: Smooth Upsampling ---
class Upsample(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.conv = nn.Conv2d(dim, dim, 3, padding=1)
    def forward(self, x):
        # Nearest + Conv is cleaner than TransposeConv
        x = F.interpolate(x, scale_factor=2, mode="nearest")
        return self.conv(x)

class Downsample(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.conv = nn.Conv2d(dim, dim, 3, stride=2, padding=1)
    def forward(self, x):
        return self.conv(x)

class ResBlock(nn.Module):
    def __init__(self, in_channels, out_channels, time_emb_dim=None):
        super().__init__()
        self.norm1 = nn.GroupNorm(32, in_channels)
        self.act1 = Swish()
        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, padding=1)
        self.time_emb = nn.Linear(time_emb_dim, out_channels) if time_emb_dim else None
        self.norm2 = nn.GroupNorm(32, out_channels)
        self.act2 = Swish()
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, padding=1)
        self.shortcut = nn.Conv2d(in_channels, out_channels, 1) if in_channels != out_channels else nn.Identity()
        self.apply(init_weights)
    def forward(self, x, t_emb=None):
        h = self.conv1(self.act1(self.norm1(x)))
        if t_emb is not None: h += self.time_emb(Swish()(t_emb))[:, :, None, None]
        h = self.conv2(self.act2(self.norm2(h)))
        return h + self.shortcut(x)

class AttentionBlock(nn.Module):
    def __init__(self, channels, num_heads=4):
        super().__init__()
        self.norm = nn.GroupNorm(32, channels)
        self.qkv = nn.Conv2d(channels, channels * 3, 1, bias=False)
        self.proj = nn.Conv2d(channels, channels, 1)
        self.num_heads = num_heads
        self.apply(init_weights)
    def forward(self, x):
        B, C, H, W = x.shape
        h = self.norm(x)
        qkv = self.qkv(h)
        q, k, v = qkv.chunk(3, dim=1)
        q = q.reshape(B, self.num_heads, -1, H * W).permute(0, 1, 3, 2)
        k = k.reshape(B, self.num_heads, -1, H * W).permute(0, 1, 2, 3)
        v = v.reshape(B, self.num_heads, -1, H * W).permute(0, 1, 3, 2)
        attn = torch.matmul(q, k) * (int(C / self.num_heads) ** -0.5)
        attn = F.softmax(attn, dim=-1)
        h = torch.matmul(attn, v)
        h = h.permute(0, 1, 3, 2).reshape(B, C, H, W)
        return x + self.proj(h)

# --- LOSSES ---
class TVLoss(nn.Module):
    "Total Variation: Punishes pixel noise"
    def forward(self, x):
        batch_size = x.size()[0]
        h_x = x.size()[2]
        w_x = x.size()[3]
        count_h = self._tensor_size(x[:, :, 1:, :])
        count_w = self._tensor_size(x[:, :, :, 1:])
        h_tv = torch.pow((x[:, :, 1:, :] - x[:, :, :h_x - 1, :]), 2).sum()
        w_tv = torch.pow((x[:, :, :, 1:] - x[:, :, :, :w_x - 1]), 2).sum()
        return 2 * (h_tv / count_h + w_tv / count_w) / batch_size
    def _tensor_size(self, t):
        return t.size()[1] * t.size()[2] * t.size()[3]

class CharbonnierLoss(nn.Module):
    def __init__(self, eps=1e-3):
        super(CharbonnierLoss, self).__init__()
        self.eps = eps
    def forward(self, x, y):
        diff = x - y
        loss = torch.sqrt(diff * diff + self.eps * self.eps)
        return torch.mean(loss)

class SSIMLoss(nn.Module):
    def __init__(self, window_size=11):
        super().__init__()
        self.window_size = window_size
        self.channel = 3
        self.window = self.create_window(window_size, self.channel)
    def gaussian(self, window_size, sigma):
        gauss = torch.Tensor([math.exp(-(x - window_size // 2) ** 2 / float(2 * sigma ** 2)) for x in range(window_size)])
        return gauss / gauss.sum()
    def create_window(self, window_size, channel):
        _1D_window = self.gaussian(window_size, 1.5).unsqueeze(1)
        _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
        window = _2D_window.expand(channel, 1, window_size, window_size).contiguous()
        return window
    def forward(self, img1, img2):
        img1 = (img1 + 1) / 2; img2 = (img2 + 1) / 2
        if img1.is_cuda: self.window = self.window.cuda(img1.get_device())
        mu1 = F.conv2d(img1, self.window, padding=self.window_size//2, groups=self.channel)
        mu2 = F.conv2d(img2, self.window, padding=self.window_size//2, groups=self.channel)
        mu1_sq = mu1.pow(2); mu2_sq = mu2.pow(2); mu1_mu2 = mu1 * mu2
        sigma1_sq = F.conv2d(img1*img1, self.window, padding=self.window_size//2, groups=self.channel) - mu1_sq
        sigma2_sq = F.conv2d(img2*img2, self.window, padding=self.window_size//2, groups=self.channel) - mu2_sq
        sigma12 = F.conv2d(img1*img2, self.window, padding=self.window_size//2, groups=self.channel) - mu1_mu2
        C1 = 0.01**2; C2 = 0.03**2
        ssim_map = ((2*mu1_mu2 + C1)*(2*sigma12 + C2))/((mu1_sq + mu2_sq + C1)*(sigma1_sq + sigma2_sq + C2))
        return 1 - ssim_map.mean()

class VGGPerceptualLoss(nn.Module):
    def __init__(self):
        super().__init__()
        vgg = torchvision.models.vgg19(weights=torchvision.models.VGG19_Weights.DEFAULT).features
        self.slice = nn.Sequential(*[vgg[x] for x in range(16)])
        for param in self.parameters(): param.requires_grad = False
    def forward(self, x, y):
        x = (x + 1) / 2; y = (y + 1) / 2
        mean = torch.tensor([0.485, 0.456, 0.406]).view(1,3,1,1).to(x.device)
        std = torch.tensor([0.229, 0.224, 0.225]).view(1,3,1,1).to(x.device)
        x = (x - mean) / std; y = (y - mean) / std
        return F.l1_loss(self.slice(x), self.slice(y))
