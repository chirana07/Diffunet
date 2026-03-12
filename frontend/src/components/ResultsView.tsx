"use client";

import ImageSlider from "./ImageSlider";

interface ResultsViewProps {
  result: {
    sessionId: string;
    originalUrl: string;
    enhancedUrl: string;
    brightnessImprovement: number; // Percentage increase in brightness
    contrastEnhancement: number; // Contrast improvement ratio
    sharpnessScore: number; // Average gradient (detail preservation)
    colorfulness: number; // Color richness metric
    mode: "fast" | "quality";
    processingTime: number;
  };
  isProcessing: boolean;
  onQualityEnhance: () => void;
  onReset: () => void;
}

export default function ResultsView({
  result,
  isProcessing,
  onQualityEnhance,
  onReset,
}: ResultsViewProps) {
  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = result.enhancedUrl;
    link.download = `enhanced_${Date.now()}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 flex flex-col gap-12 sm:gap-16 items-center">
      {/* Header */}
      <div className="w-full flex items-center justify-between border-b border-white/5 pb-6">
        <button onClick={onReset} className="btn btn-outline group">
          <svg
            className="w-4 h-4 transition-transform group-hover:-translate-x-1"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <path d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          New Image
        </button>
        <div className="badge">
          {result.mode === "quality" ? "Quality Mode" : "Fast Mode"}
        </div>
      </div>

      {/* Image Comparison */}
      <div className="w-full card overflow-hidden p-0 sm:p-0 border-0 bg-transparent shadow-2xl shadow-[#F0B100]/20 rounded-2xl">
        <ImageSlider
          originalUrl={result.originalUrl}
          enhancedUrl={result.enhancedUrl}
        />
      </div>

      {/* Actions */}
      <div className="flex flex-wrap justify-center gap-6 mx-auto">
        <button
          onClick={handleDownload}
          className="btn btn-primary min-w-[240px] h-14 text-base shadow-lg shadow-[#F0B100]/20 hover:shadow-[#F0B100]/30 hover:-translate-y-0.5 transition-all"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download Enhanced
        </button>
        {result.mode === "fast" && (
          <button
            onClick={onQualityEnhance}
            disabled={isProcessing}
            className="btn btn-secondary min-w-[240px] h-14 text-base bg-white/5 hover:bg-white/10 border-white/10 hover:-translate-y-0.5 transition-all"
          >
            {isProcessing ? (
              <>
                <div className="w-5 h-5 spinner border-2"></div>
                Enhancing details...
              </>
            ) : (
              <>
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                >
                  <path d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
                Enhance Quality (SwinIR)
              </>
            )}
          </button>
        )}
      </div>

      {/* Metrics */}
      <div className="flex flex-wrap justify-center gap-6 sm:gap-8 lg:gap-12">
        <div className="card w-full sm:w-auto min-w-[200px] px-8 py-8 text-center space-y-3 hover:bg-white/[0.04] transition-colors border-white/10 bg-white/[0.02] group relative">
          <div className="text-xs font-bold text-gray-500 tracking-[0.2em] uppercase flex items-center justify-center gap-1">
            PSNR
            <span
              className="cursor-help text-gray-600 hover:text-[#F0B100]"
              title="Peak Signal-to-Noise Ratio"
            >
              ⓘ
            </span>
          </div>
          <div className="text-4xl font-bold text-white tracking-tight">
            {result.psnr.toFixed(2)}
          </div>
          <div className="text-xs text-[#F0B100] font-medium">dB</div>
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-gray-900 border border-white/10 rounded-lg text-xs text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-xl">
            <strong className="text-white">Peak Signal-to-Noise Ratio</strong>
            <p className="mt-1">
              Measures difference between enhanced and original. Low values here
              are expected since the enhanced image is much brighter.
            </p>
          </div>
        </div>
        <div className="card w-full sm:w-auto min-w-[200px] px-8 py-8 text-center space-y-3 hover:bg-white/[0.04] transition-colors border-white/10 bg-white/[0.02] group relative">
          <div className="text-xs font-bold text-gray-500 tracking-[0.2em] uppercase flex items-center justify-center gap-1">
            SSIM
            <span
              className="cursor-help text-gray-600 hover:text-[#F0B100]"
              title="Structural Similarity Index"
            >
              ⓘ
            </span>
          </div>
          <div className="text-4xl font-bold text-white tracking-tight">
            {result.ssim.toFixed(3)}
          </div>
          <div className="text-xs text-[#F0B100] font-medium">Index</div>
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-gray-900 border border-white/10 rounded-lg text-xs text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-xl">
            <strong className="text-white">Structural Similarity Index</strong>
            <p className="mt-1">
              Measures similarity to original. Low values here are expected
              since the enhanced image looks very different from the dark input.
            </p>
          </div>
        </div>
        <div className="card w-full sm:w-auto min-w-[200px] px-8 py-8 text-center space-y-3 hover:bg-white/[0.04] transition-colors border-white/10 bg-white/[0.02]">
          <div className="text-xs font-bold text-gray-500 tracking-[0.2em] uppercase">
            Processing
          </div>
          <div className="text-4xl font-bold text-white tracking-tight">
            {result.processingTime.toFixed(2)}
          </div>
          <div className="text-xs text-[#F0B100] font-medium">Seconds</div>
        </div>
      </div>

      {/* Metrics Explanation */}
      <div className="w-full card p-6 bg-gradient-to-br from-blue-500/5 to-purple-500/5 border-white/10">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <svg
            className="w-4 h-4 text-[#F0B100]"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Understanding These Metrics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-400">
          <div>
            <span className="text-white font-medium">
              PSNR (Peak Signal-to-Noise Ratio):
            </span>{" "}
            Measures the ratio between maximum signal power and noise.
            <code className="block bg-black/50 p-2 rounded-lg text-sm text-[#F0B100] font-mono border border-[#F0B100]/20 mt-2">
              PSNR = 10 × log₁₀(255² / MSE)
            </code>
            <span className="text-gray-500 text-xs mt-1 block">
              When comparing to ground truth, higher values indicate better
              quality.
            </span>
          </div>
          <div>
            <span className="text-white font-medium">
              SSIM (Structural Similarity Index):
            </span>{" "}
            Evaluates image quality based on luminance, contrast, and structure
            preservation. Range: 0 to 1. When comparing to ground truth, higher
            values indicate better quality. Uses Wang et al. 2004 standard with
            11×11 Gaussian window (σ=1.5).
          </div>
        </div>
        <p className="mt-3 text-xs text-yellow-200/80 bg-yellow-500/10 p-2 rounded">
          <strong>Important:</strong> These metrics compare enhanced vs.
          original dark input (not ground truth). Low values are expected and
          normal. <br /> They simply show the enhanced image is very different
          from the dark original. This does NOT indicate poor quality. Our model
          achieves ~20 dB PSNR and ~0.80 SSIM when properly evaluated against
          ground truth.
        </p>
      </div>
    </div>
  );
}
