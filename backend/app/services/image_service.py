"""
Image Processing Service

NOTE: This local backend is not used when NEXT_PUBLIC_BACKEND_URL points to Kaggle/ngrok.
The frontend calls Kaggle directly for inference. This file is kept as a fallback only.
"""

import os
import time
import random
import asyncio
from io import BytesIO
from typing import Dict, Any, Optional

from PIL import Image
import numpy as np


class ImageService:
    """Service for processing and enhancing images (local placeholder)."""

    def __init__(self):
        self.upload_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "uploads"
        )
        os.makedirs(self.upload_dir, exist_ok=True)
        self.base_url = os.environ.get("BACKEND_BASE_URL", "http://localhost:8000")

    async def process_fast(
        self,
        contents: bytes,
        session_id: str,
        extension: str,
    ) -> Dict[str, Any]:
        start_time = time.time()

        original_filename = f"{session_id}_original.{extension}"
        original_path = os.path.join(self.upload_dir, original_filename)
        with open(original_path, "wb") as f:
            f.write(contents)

        img = Image.open(BytesIO(contents))
        enhanced_img = await self._apply_fast_enhancement(img)

        enhanced_filename = f"{session_id}_fast.{extension}"
        enhanced_path = os.path.join(self.upload_dir, enhanced_filename)
        enhanced_img.save(enhanced_path)

        psnr, ssim = self._calculate_mock_metrics(mode="fast")

        return {
            "original_url": f"{self.base_url}/uploads/{original_filename}",
            "enhanced_url": f"{self.base_url}/uploads/{enhanced_filename}",
            "psnr": psnr,
            "ssim": ssim,
            "processing_time": round(time.time() - start_time, 2),
        }

    async def process_quality(self, session_id: str) -> Dict[str, Any]:
        start_time = time.time()

        original_path = self._find_original(session_id)
        if not original_path:
            raise FileNotFoundError("Original image not found")

        img = Image.open(original_path)
        extension = original_path.split(".")[-1]

        await asyncio.sleep(random.uniform(1.0, 2.0))
        enhanced_img = await self._apply_quality_enhancement(img)

        enhanced_filename = f"{session_id}_quality.{extension}"
        enhanced_path = os.path.join(self.upload_dir, enhanced_filename)
        enhanced_img.save(enhanced_path)

        psnr, ssim = self._calculate_mock_metrics(mode="quality")

        return {
            "enhanced_url": f"{self.base_url}/uploads/{enhanced_filename}",
            "psnr": psnr,
            "ssim": ssim,
            "processing_time": round(time.time() - start_time, 2),
        }

    async def _apply_fast_enhancement(self, img: Image.Image) -> Image.Image:
        await asyncio.sleep(random.uniform(0.5, 1.0))
        img_array = np.array(img).astype(float)
        enhanced = np.clip(img_array * 1.3, 0, 255).astype(np.uint8)
        return Image.fromarray(enhanced)

    async def _apply_quality_enhancement(self, img: Image.Image) -> Image.Image:
        img_array = np.array(img).astype(float)
        enhanced = np.power(np.clip(img_array * 1.5, 0, 255) / 255.0, 0.85) * 255.0
        enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
        return Image.fromarray(enhanced)

    def _find_original(self, session_id: str) -> Optional[str]:
        for filename in os.listdir(self.upload_dir):
            if filename.startswith(session_id) and "_original" in filename:
                return os.path.join(self.upload_dir, filename)
        return None

    def _calculate_mock_metrics(self, mode: str) -> tuple[float, float]:
        if mode == "quality":
            return round(random.uniform(28.0, 42.0), 2), round(random.uniform(0.88, 0.99), 4)
        return round(random.uniform(20.0, 35.0), 2), round(random.uniform(0.75, 0.95), 4)
