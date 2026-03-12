"use client";

import { useState, useCallback } from "react";
import Header from "@/components/Header";
import DropZone from "@/components/DropZone";
import ResultsView from "@/components/ResultsView";

interface EnhanceResult {
  sessionId: string;
  originalUrl: string;
  enhancedUrl: string;
  psnr: number;
  ssim: number;
  mode: "fast" | "quality";
  processingTime: number;
}

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "https://nonascetical-unapproved-emmie.ngrok-free.dev";

export default function Home() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<EnhanceResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = useCallback(async (file: File) => {
    setIsProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("image", file);

      const response = await fetch(`${BACKEND_URL}/api/enhance/fast`, {
        method: "POST",
        body: formData,
        headers: {
          "ngrok-skip-browser-warning": "true",
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Enhancement failed");
      }

      setResult({
        sessionId: data.session_id,
        originalUrl: data.original_url,
        enhancedUrl: data.image_url,
        psnr: data.psnr,
        ssim: data.ssim,
        mode: "fast",
        processingTime: data.processing_time,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const handleQualityEnhance = useCallback(async () => {
    if (!result) return;

    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch(`${BACKEND_URL}/api/enhance/quality`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify({ session_id: result.sessionId }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Quality enhancement failed");
      }

      setResult((prev) =>
        prev
          ? {
              ...prev,
              enhancedUrl: data.image_url,
              psnr: data.psnr,
              ssim: data.ssim,
              mode: "quality",
              processingTime: data.processing_time,
            }
          : null,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsProcessing(false);
    }
  }, [result]);

  const handleReset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex flex-col">
      <Header />

      <main className="flex-1 relative z-10 w-full flex items-center justify-center">
        <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-10 py-20 sm:py-24 lg:py-28 w-full">
          {!result ? (
            <div className="space-y-24 sm:space-y-28 lg:space-y-32 flex flex-col items-center">
              {/* Hero Section */}
              <section className="text-center pt-8 sm:pt-12 pb-10 w-full max-w-3xl mx-auto">
                <div className="hero-badge inline-flex items-center gap-3 rounded-full bg-[#F0B100]/15 border border-[#F0B100]/30 mb-14">
                  <span className="w-2 h-2 rounded-full bg-[#F0B100] animate-pulse"></span>
                  <span className="text-sm font-medium text-[#F0B100]">
                    AI-Powered Enhancement
                  </span>
                </div>

                <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-10 leading-tight">
                  Low-Light Image{" "}
                  <span className="gradient-text">Restoration</span>
                </h1>

                <p className="text-base sm:text-lg text-gray-400 max-w-2xl mx-auto mt-6">
                  Deep learning enhancement with quantitative quality metrics
                </p>
              </section>

              {/* Upload Section */}
              <section className="w-full flex justify-center">
                <DropZone
                  onUpload={handleUpload}
                  isProcessing={isProcessing}
                  error={error}
                />
              </section>

              {/* Spacer */}
              <div className="h-8 sm:h-12"></div>

              {/* Metrics Info Section */}
              <section className="w-full max-w-4xl mx-auto">
                <div className="card p-6 sm:p-8 bg-gradient-to-br from-white/[0.02] to-white/[0.01] border-white/10">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <svg
                      className="w-5 h-5 text-[#F0B100]"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      viewBox="0 0 24 24"
                    >
                      <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Quality Metrics Explained
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                    <div className="space-y-2">
                      <h4 className="font-medium text-[#F0B100]">
                        PSNR (Peak Signal-to-Noise Ratio)
                      </h4>
                      <p className="text-gray-400">
                        Measures the ratio between maximum signal power and
                        noise. Calculated as:
                      </p>
                      <code className="block bg-black/50 p-3 rounded-lg text-sm text-[#F0B100] font-mono border border-[#F0B100]/20">
                        PSNR = 10 × log₁₀(255² / MSE)
                      </code>
                      <p className="text-gray-500 text-xs">
                        Higher values traditionally indicate better quality when
                        compared to ground truth.
                      </p>
                    </div>
                    <div className="space-y-2">
                      <h4 className="font-medium text-[#F0B100]">
                        SSIM (Structural Similarity Index)
                      </h4>
                      <p className="text-gray-400">
                        Evaluates image quality based on luminance, contrast,
                        and structure preservation.
                      </p>
                      <p className="text-gray-500 text-xs mt-2">
                        Based on Wang et al. (2004) with 11×11 Gaussian window
                        (σ=1.5), stability constants K₁=0.01, K₂=0.03.
                      </p>
                      <p className="text-gray-500 text-xs">
                        Range: 0 to 1. Higher values indicate better quality
                        when compared to ground truth (1 = identical images, is
                        considered good).
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <p className="text-xs text-yellow-200/80">
                      <strong>Important:</strong> In this app, metrics compare
                      enhanced vs. original dark input (not ground truth). Low
                      values are expected and normal. <br /> They simply show
                      the enhanced image is very different from the dark
                      original. This does NOT indicate poor quality. Our model
                      achieves ~20 dB PSNR and ~0.80 SSIM when properly
                      evaluated against ground truth.
                    </p>
                  </div>
                </div>
              </section>
            </div>
          ) : (
            <ResultsView
              result={result}
              isProcessing={isProcessing}
              onQualityEnhance={handleQualityEnhance}
              onReset={handleReset}
            />
          )}
        </div>
      </main>

      <footer className="relative z-10 border-t border-white/5 py-3 sm:py-4 w-full flex justify-center">
        <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-10 w-full flex flex-col items-center">
          <div className="flex flex-col items-center gap-1.5 text-center text-sm text-gray-400">
            <p>
              Powered by{" "}
              <span className="text-[#F0B100] font-medium">Zero-DCE</span> &{" "}
              <span className="text-[#E17100] font-medium">SwinIR</span>
            </p>
            <p className="text-xs text-gray-500">
              © 2025 LUMIAI. Academic Project.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
