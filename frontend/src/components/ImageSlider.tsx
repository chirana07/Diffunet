"use client";

import { useState, useRef, useCallback } from "react";

interface ImageSliderProps {
  originalUrl: string;
  enhancedUrl: string;
}

export default function ImageSlider({
  originalUrl,
  enhancedUrl,
}: ImageSliderProps) {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const updateSliderPosition = useCallback((clientX: number) => {
    if (!containerRef.current) return;

    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPosition(percentage);
  }, []);

  const handleMouseDown = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (isDragging) {
        updateSliderPosition(e.clientX);
      }
    },
    [isDragging, updateSliderPosition],
  );

  const handleTouchStart = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleTouchEnd = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (isDragging && e.touches[0]) {
        updateSliderPosition(e.touches[0].clientX);
      }
    },
    [isDragging, updateSliderPosition],
  );

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      updateSliderPosition(e.clientX);
    },
    [updateSliderPosition],
  );

  return (
    <div
      ref={containerRef}
      className={`relative w-full aspect-video bg-black/40 rounded-lg overflow-hidden select-none ${
        isDragging ? "cursor-grabbing" : "cursor-grab"
      }`}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseUp}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onTouchMove={handleTouchMove}
      onClick={handleClick}
    >
      {/* Enhanced Image (Background) */}
      <img
        src={enhancedUrl}
        alt="Enhanced image"
        className="absolute inset-0 w-full h-full object-contain pointer-events-none"
        draggable={false}
      />

      {/* Original Image (Clipped) */}
      <div
        className="absolute inset-0 overflow-hidden"
        style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
      >
        <img
          src={originalUrl}
          alt="Original low-light image"
          className="absolute inset-0 w-full h-full object-contain pointer-events-none"
          draggable={false}
        />
      </div>

      {/* Slider Divider Line */}
      <div
        className="absolute inset-y-0 w-0.5 bg-white/90 shadow-lg"
        style={{ left: `${sliderPosition}%` }}
      >
        {/* Slider Handle */}
        <div
          className={`absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-12 h-12 rounded-full bg-white shadow-2xl flex items-center justify-center transition-all duration-200 ${
            isDragging ? "scale-110 shadow-[#F0B100]/50" : "hover:scale-105"
          }`}
        >
          <svg
            className="w-6 h-6 text-gray-900"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            viewBox="0 0 24 24"
          >
            <path d="M8 9l4-4 4 4M16 15l-4 4-4-4" />
          </svg>
        </div>
      </div>

      {/* Labels */}
      <div className="absolute bottom-4 left-4 px-3 py-1.5 rounded-lg bg-black/70 backdrop-blur-sm border border-white/10">
        <span className="text-xs font-medium text-white">Original</span>
      </div>
      <div className="absolute bottom-4 right-4 px-3 py-1.5 rounded-lg bg-black/70 backdrop-blur-sm border border-white/10">
        <span className="text-xs font-medium text-white">Enhanced</span>
      </div>

      {/* Position Indicator (Optional) */}
      {isDragging && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 px-3 py-1.5 rounded-lg bg-[#F0B100]/90 backdrop-blur-sm border border-[#F0B100]/30">
          <span className="text-xs font-semibold text-white">
            {Math.round(sliderPosition)}%
          </span>
        </div>
      )}
    </div>
  );
}
