"use client";

const features = [
  {
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    title: "Fast Mode",
    desc: "Zero-DCE network for instant brightness correction",
    color: "from-cyan-400 to-blue-500",
  },
  {
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
      </svg>
    ),
    title: "Quality Mode",
    desc: "SwinIR transformer for maximum detail recovery",
    color: "from-[#F0B100] to-[#E17100]",
  },
];

export default function FeatureCards() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 sm:gap-8 max-w-4xl mx-auto">
      {features.map((f, i) => (
        <div key={i} className="card p-7 group">
          <div
            className={`inline-flex items-center justify-center w-14 h-14 rounded-xl bg-linear-to-br ${f.color} mb-5`}
          >
            <div className="w-7 h-7 text-white">{f.icon}</div>
          </div>

          <h3 className="text-base font-semibold text-white mb-2.5">
            {f.title}
          </h3>
          <p className="text-sm text-gray-400 leading-relaxed">{f.desc}</p>
        </div>
      ))}
    </div>
  );
}
