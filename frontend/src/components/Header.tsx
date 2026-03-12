"use client";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-[#0a0a0f]/80 backdrop-blur-md border-b border-white/5">
      <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-10">
        <div className="flex items-center h-24">
          <div className="flex items-center gap-4">
            <div className="w-9 h-9 rounded-lg bg-linear-to-br from-[#F0B100] to-[#E17100] flex items-center justify-center">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-white">LUMIAI</h1>
              <div className="badge text-[0.7rem] sm:text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                Beta
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
