"use client";

import { useCallback, useState, useRef } from "react";

const API_URL = "https://gleamingly-limitary-georgie.ngrok-free.dev/"; // Kaggle backend URL

export async function enhanceImage(file: File) {
  const formData = new FormData();
  formData.append("image", file);
  const res = await fetch(`${API_URL}/api/enhance/fast`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to enhance image");
  return await res.json();
}

interface DropZoneProps {
  onUpload: (file: File) => void;
  isProcessing: boolean;
  error: string | null;
}

export default function DropZone({
  onUpload,
  isProcessing,
  error,
}: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndUpload = (file: File) => {
    if (!file.type.startsWith("image/")) {
      alert("Please upload an image file");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert("Max file size is 5MB");
      return;
    }
    onUpload(file);
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div
        onClick={() => !isProcessing && fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setIsDragging(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          const files = e.dataTransfer.files;
          if (files[0]) validateAndUpload(files[0]);
        }}
        className={`card p-14 sm:p-16 cursor-pointer transition-all ${
          isDragging
            ? "border-[#F0B100]/50 bg-[#F0B100]/5"
            : "hover:border-white/10"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={(e) =>
            e.target.files?.[0] && validateAndUpload(e.target.files[0])
          }
          className="hidden"
        />

        {isProcessing ? (
          <div className="text-center space-y-4">
            <div className="w-16 h-16 mx-auto spinner"></div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-1">
                Processing Image
              </h3>
              <p className="text-sm text-gray-400">
                Enhancing with AI models...
              </p>
            </div>
          </div>
        ) : (
          <div className="text-center space-y-10">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-[#F0B100]/10 border-2 border-dashed border-[#F0B100]/30">
              <svg
                className="w-10 h-10 text-[#F0B100]"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-white">Upload Image</h3>
              <p className="text-sm text-gray-400">
                Drop your image here or{" "}
                <span className="text-[#F0B100] font-medium">
                  browse files
                </span>
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-6 pt-5">
              <span className="chip rounded-xl bg-white/10 text-sm text-gray-200 border border-white/20">
                JPG, PNG
              </span>
              <span className="chip rounded-xl bg-white/10 text-sm text-gray-200 border border-white/20">
                Max 5MB
              </span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-5 p-5 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-4">
          <svg
            className="w-5 h-5 text-red-400 shrink-0 mt-0.5"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-medium text-red-300">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
}
