"use client";

import { useState } from "react";

import Header from "@/components/Header";
import ImageSlider from "@/components/ImageSlider";
import DropZone, { enhanceImage } from "@/components/DropZone";

export default function Demo() {
  const [showDemo, setShowDemo] = useState(true);

    const [result, setResult] = useState<any>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleUpload = async (file: File) => {
      setIsProcessing(true);
      setError(null);
      try {
        const data = await enhanceImage(file);
        setResult(data);
      } catch (e: any) {
        setError(e.message);
      }
      setIsProcessing(false);
    };

    return (
      <div className="min-h-screen bg-[#0a0a0f] flex flex-col">
        <Header />
        <main className="flex-1 relative z-10 w-full flex items-center justify-center">
          <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-10 py-20 sm:py-24 lg:py-28 w-full">
            <div className="w-full max-w-5xl mx-auto space-y-10">
              <DropZone onUpload={handleUpload} isProcessing={isProcessing} error={error} />
              {result && (
                <div className="card overflow-hidden p-4 sm:p-6">
                  <ImageSlider
                    originalUrl={result.original_url}
                    enhancedUrl={result.image_url}
                  />
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    );
                    >
                      ⓘ
                    </span>
                  </div>
                  <div className="text-2xl font-bold text-white">
                    {demoResult.psnr.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">dB</div>
                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 p-3 bg-gray-900 border border-white/10 rounded-lg text-xs text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-xl">
                    <strong className="text-white">
                      Peak Signal-to-Noise Ratio
                    </strong>
                    <p className="mt-1">
                      Measures difference from original. Low values expected
                      when comparing enhanced vs dark input.
                    </p>
                  </div>
                </div>
                <div className="card p-6 text-center group relative">
                  <div className="text-xs text-gray-400 mb-2 flex items-center justify-center gap-1">
                    SSIM
                    <span
                      className="cursor-help text-gray-600 hover:text-[#F0B100]"
                      title="Structural Similarity Index"
                    >
                      ⓘ
                    </span>
                  </div>
                  <div className="text-2xl font-bold text-white">
                    {demoResult.ssim.toFixed(3)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Index</div>
                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 p-3 bg-gray-900 border border-white/10 rounded-lg text-xs text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-xl">
                    <strong className="text-white">
                      Structural Similarity Index
                    </strong>
                    <p className="mt-1">
                      Measures similarity to original. Low values expected since
                      enhanced image looks very different.
                    </p>
                  </div>
                </div>
                <div className="card p-6 text-center">
                  <div className="text-xs text-gray-400 mb-2">Time</div>
                  <div className="text-2xl font-bold text-white">
                    {demoResult.processingTime.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">sec</div>
                </div>
              </div>

              {/* Metrics Explanation */}
              <div className="card p-6 bg-gradient-to-br from-blue-500/5 to-purple-500/5 border-white/10">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <svg
                    className="w-5 h-5 text-[#F0B100]"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                  >
                    <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Understanding Image Quality Metrics
                </h3>
                <div className="space-y-4 text-sm text-gray-300">
                  <div className="p-4 bg-white/5 rounded-lg">
                    <h4 className="font-medium text-white mb-2">
                      PSNR (Peak Signal-to-Noise Ratio)
                    </h4>
                    <p className="text-gray-400 mb-2">
                      PSNR measures the ratio between the maximum possible
                      signal power and the noise (error) power. It&apos;s
                      calculated using:
                    </p>
                    <code className="block bg-black/50 p-3 rounded-lg text-sm text-[#F0B100] font-mono border border-[#F0B100]/20">
                      PSNR = 10 × log₁₀(MAX² / MSE)
                    </code>
                    <p className="text-gray-400 mt-2 text-sm">
                      Where MAX is the maximum pixel value (255 for 8-bit
                      images) and MSE is Mean Squared Error between images.
                    </p>
                  </div>
                  <div className="p-4 bg-white/5 rounded-lg">
                    <h4 className="font-medium text-white mb-2">
                      SSIM (Structural Similarity Index)
                    </h4>
                    <p className="text-gray-400 mb-2">
                      SSIM evaluates image quality based on three components:
                      luminance, contrast, and structure. Developed by Wang et
                      al. (2004), it better correlates with human perception
                      than PSNR. Range: 0 to 1. Higher values indicate better
                      quality when compared to ground truth (1 = identical
                      images, ~0.80+ is considered good).
                    </p>
                    <ul className="text-sm text-gray-400 space-y-1 mt-2">
                      <li>
                        • <span className="text-gray-300">Window size:</span>{" "}
                        11×11 (adaptive for small images)
                      </li>
                      <li>
                        •{" "}
                        <span className="text-gray-300">
                          Gaussian weighting:
                        </span>{" "}
                        σ = 1.5
                      </li>
                      <li>
                        •{" "}
                        <span className="text-gray-300">
                          Stability constants:
                        </span>{" "}
                        K₁ = 0.01, K₂ = 0.03
                      </li>
                    </ul>
                  </div>
                  <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <p className="text-sm text-yellow-200/90">
                      <strong>Important:</strong> In this application, metrics
                      compare the enhanced output vs. the original dark input
                      (not ground truth). Low values are expected and normal -
                      they simply show the enhanced image is very different from
                      the dark original. This does NOT indicate poor quality.
                      Our model achieves ~20 dB PSNR and ~0.80 SSIM when
                      properly evaluated against ground truth.
                    </p>
                  </div>
                </div>
              </div>

              {/* Features */}
              <div className="card p-6 bg-gradient-to-br from-[#F0B100]/5 to-[#E17100]/5 border-[#F0B100]/20">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Component Features
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-gray-300">
                  <div className="flex items-center gap-2">
                    <span className="text-green-400">✓</span>
                    <span>Smooth drag interactions</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-green-400">✓</span>
                    <span>Mouse and touch support</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-green-400">✓</span>
                    <span>Responsive design</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-green-400">✓</span>
                    <span>Visual feedback on drag</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-green-400">✓</span>
                    <span>Reusable component</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-green-400">✓</span>
                    <span>Premium animations</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="relative z-10 border-t border-white/5 py-3 sm:py-4 w-full">
        <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-10 w-full">
          <div className="flex flex-col items-center gap-1.5 text-center text-sm text-gray-400">
            <p>
              Image Slider Demo -{" "}
              <span className="text-[#F0B100] font-medium">
                AI-Powered Enhancement
              </span>
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
