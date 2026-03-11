
import torch
import torch.nn as nn
from modules import ResBlock, AttentionBlock, get_timestep_embedding, Swish, Upsample, Downsample
from config import Config

class PureDiffusionUNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conf = Config()
        ch = self.conf.CHANNELS        
        ch_mult = self.conf.CHANNEL_MULT 
        
        self.time_mlp = nn.Sequential(nn.Linear(ch, ch * 4), Swish(), nn.Linear(ch * 4, ch * 4))
        self.head = nn.Conv2d(6, ch, 3, padding=1)
        self.downs = nn.ModuleList()
        curr_ch = ch
        feat_chs = [curr_ch]
        
        # Encoder
        for idx, mult in enumerate(ch_mult):
            out_ch = ch * mult
            for _ in range(self.conf.RES_BLOCKS):
                self.downs.append(ResBlock(curr_ch, out_ch, ch*4))
                curr_ch = out_ch
                feat_chs.append(curr_ch)
                if idx == len(ch_mult) - 1: 
                    self.downs.append(AttentionBlock(curr_ch))
            if idx != len(ch_mult) - 1:
                self.downs.append(Downsample(curr_ch)) # Smooth Downsample
                feat_chs.append(curr_ch)

        # Bottleneck
        self.mid1 = ResBlock(curr_ch, curr_ch, ch*4)
        self.mid_attn = AttentionBlock(curr_ch)
        self.mid2 = ResBlock(curr_ch, curr_ch, ch*4)

        # Decoder
        self.ups = nn.ModuleList()
        for idx, mult in reversed(list(enumerate(ch_mult))):
            out_ch = ch * mult
            for _ in range(self.conf.RES_BLOCKS):
                skip_ch = feat_chs.pop()
                self.ups.append(ResBlock(curr_ch + skip_ch, out_ch, ch*4))
                curr_ch = out_ch
                if idx == len(ch_mult) - 1: 
                    self.ups.append(AttentionBlock(curr_ch))
            if idx != 0:
                self.ups.append(Upsample(curr_ch)) # Smooth Upsample
                
        self.final = nn.Sequential(nn.GroupNorm(32, curr_ch), Swish(), nn.Conv2d(curr_ch, 3, 3, padding=1))
        
    def forward(self, x, t, low_light):
        t_emb = self.time_mlp(get_timestep_embedding(t, self.conf.CHANNELS))
        x_in = torch.cat([x, low_light], dim=1)
        h = self.head(x_in)
        skips = [h]
        for layer in self.downs:
            h = layer(h, t_emb) if isinstance(layer, ResBlock) else layer(h)
            if not isinstance(layer, AttentionBlock): skips.append(h)
        h = self.mid1(h, t_emb)
        h = self.mid_attn(h)
        h = self.mid2(h, t_emb)
        for layer in self.ups:
            if isinstance(layer, ResBlock):
                skip = skips.pop()
                if skip.shape[2:] != h.shape[2:]: skip = torch.nn.functional.interpolate(skip, size=h.shape[2:])
                h = torch.cat([h, skip], dim=1)
                h = layer(h, t_emb)
            elif isinstance(layer, Upsample): h = layer(h)
            else: h = layer(h)
        return self.final(h)
