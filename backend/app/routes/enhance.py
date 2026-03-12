"""
Image Enhancement Routes
"""

import os
import uuid
import time
import random
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.image_service import ImageService


router = APIRouter()
image_service = ImageService()


class QualityEnhanceRequest(BaseModel):
    """Request model for quality enhancement."""
    session_id: str


class EnhanceResponse(BaseModel):
    """Response model for enhancement endpoints."""
    success: bool
    session_id: str
    original_url: Optional[str] = None
    image_url: str
    psnr: float
    ssim: float
    mode: str
    processing_time: float


@router.post("/enhance/fast", response_model=EnhanceResponse)
async def enhance_fast(image: UploadFile = File(...)):
    """
    Fast Mode Enhancement Endpoint (Zero-DCE)
    
    Accepts image file and returns enhanced image with metrics.
    Processing time: < 15 seconds
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png"]
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPG and PNG allowed."
        )
    
    # Check file size (2MB max)
    contents = await image.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 2MB."
        )
    
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Get file extension
        ext = image.filename.split(".")[-1].lower() if image.filename else "jpg"
        
        # Process image
        result = await image_service.process_fast(
            contents=contents,
            session_id=session_id,
            extension=ext
        )
        
        return EnhanceResponse(
            success=True,
            session_id=session_id,
            original_url=result["original_url"],
            image_url=result["enhanced_url"],
            psnr=result["psnr"],
            ssim=result["ssim"],
            mode="fast",
            processing_time=result["processing_time"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance/quality", response_model=EnhanceResponse)
async def enhance_quality(request: QualityEnhanceRequest):
    """
    High Quality Mode Enhancement Endpoint (SwinIR)
    
    Requires session_id from previous fast enhancement.
    Processing time: 40-60 seconds
    """
    try:
        result = await image_service.process_quality(
            session_id=request.session_id
        )
        
        return EnhanceResponse(
            success=True,
            session_id=request.session_id,
            image_url=result["enhanced_url"],
            psnr=result["psnr"],
            ssim=result["ssim"],
            mode="quality",
            processing_time=result["processing_time"]
        )
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Original image not found. Please upload again."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
