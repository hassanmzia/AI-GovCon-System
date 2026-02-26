"use client";

import { AlertTriangle, CheckCircle, XCircle, Info } from "lucide-react";

interface RiskScoreData {
  legal: number;
  compliance: number;
  deadline: number;
  financial: number;
  security: number;
  reputation: number;
  composite: number;
}

interface RiskScoreDisplayProps {
  riskScore: RiskScoreData | null;
  threshold?: number;
  showDetails?: boolean;
}

const DIMENSIONS: { key: keyof Omit<RiskScoreData, "composite">; label: string }[] = [
  { key: "legal", label: "Legal" },
  { key: "compliance", label: "Compliance" },
  { key: "deadline", label: "Deadline" },
  { key: "financial", label: "Financial" },
  { key: "security", label: "Security" },
  { key: "reputation", label: "Reputation" },
];

function scoreColor(score: number): string {
  if (score <= 0.25) return "#16a34a"; // green-600
  if (score <= 0.5) return "#d97706";  // amber-600
  return "#dc2626";                     // red-600
}

function scoreBg(score: number): string {
  if (score <= 0.25) return "bg-green-100 text-green-700";
  if (score <= 0.5) return "bg-amber-100 text-amber-700";
  return "bg-red-100 text-red-700";
}

function compositeLabel(score: number, threshold: number): {
  text: string;
  icon: React.ReactNode;
  bg: string;
  border: string;
  textColor: string;
} {
  if (score < threshold) {
    return {
      text: "SAFE TO ACT",
      icon: <CheckCircle className="h-5 w-5 text-green-600" />,
      bg: "bg-green-50",
      border: "border-green-300",
      textColor: "text-green-700",
    };
  }
  if (score <= 0.5) {
    return {
      text: "REVIEW REQUIRED",
      icon: <AlertTriangle className="h-5 w-5 text-amber-600" />,
      bg: "bg-amber-50",
      border: "border-amber-300",
      textColor: "text-amber-700",
    };
  }
  return {
    text: "ACTION BLOCKED",
    icon: <XCircle className="h-5 w-5 text-red-600" />,
    bg: "bg-red-50",
    border: "border-red-300",
    textColor: "text-red-700",
  };
}

export function RiskScoreDisplay({
  riskScore,
  threshold = 0.35,
  showDetails = true,
}: RiskScoreDisplayProps) {
  if (!riskScore) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-6 flex flex-col items-center justify-center gap-2 text-gray-500">
        <Info className="h-8 w-8 text-gray-400" />
        <p className="text-sm font-medium">No risk assessment available</p>
        <p className="text-xs text-gray-400">
          Run a risk assessment to see scores
        </p>
      </div>
    );
  }

  const composite = riskScore.composite;
  const status = compositeLabel(composite, threshold);
  const compositeColorHex = scoreColor(composite);

  return (
    <div className="space-y-4">
      {/* Composite Score Display */}
      <div
        className={`rounded-lg border-2 ${status.border} ${status.bg} p-5 flex items-center justify-between`}
      >
        <div className="flex items-center gap-4">
          {/* Big score circle */}
          <div className="relative flex items-center justify-center">
            <svg width="80" height="80" viewBox="0 0 80 80">
              {/* Background circle */}
              <circle
                cx="40"
                cy="40"
                r="34"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="8"
              />
              {/* Score arc */}
              <circle
                cx="40"
                cy="40"
                r="34"
                fill="none"
                stroke={compositeColorHex}
                strokeWidth="8"
                strokeDasharray={`${composite * 213.6} 213.6`}
                strokeLinecap="round"
                transform="rotate(-90 40 40)"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span
                className="text-xl font-bold leading-none"
                style={{ color: compositeColorHex }}
              >
                {composite.toFixed(2)}
              </span>
              <span className="text-xs text-gray-500 leading-none mt-0.5">
                / 1.00
              </span>
            </div>
          </div>

          {/* Status */}
          <div>
            <div className="flex items-center gap-2 mb-1">
              {status.icon}
              <span className={`font-bold text-lg ${status.textColor}`}>
                {status.text}
              </span>
            </div>
            <p className="text-sm text-gray-600">
              Composite risk score{" "}
              <span className="font-medium">{composite.toFixed(3)}</span>
              {composite < threshold
                ? ` — below threshold (${threshold})`
                : ` — above threshold (${threshold})`}
            </p>
            <p className={`text-xs mt-1 font-medium ${status.textColor}`}>
              {composite < threshold
                ? "AI can act autonomously"
                : "Human approval required"}
            </p>
          </div>
        </div>

        {/* Threshold indicator */}
        <div className="text-right text-xs text-gray-500">
          <p className="font-medium">Threshold</p>
          <p className="text-base font-bold text-gray-700">{threshold}</p>
        </div>
      </div>

      {/* Dimension Bars */}
      {showDetails && (
        <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Risk Dimensions
          </p>
          {DIMENSIONS.map(({ key, label }) => {
            const val = riskScore[key];
            const pct = Math.round(val * 100);
            const color = scoreColor(val);
            const textClass = scoreBg(val);

            return (
              <div key={key} className="flex items-center gap-3">
                {/* Label */}
                <span className="text-sm text-gray-600 w-24 flex-shrink-0">
                  {label}
                </span>

                {/* Bar */}
                <div className="flex-1 h-5 bg-gray-100 rounded-full overflow-hidden relative">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: color,
                    }}
                  />
                  {/* Threshold marker */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-gray-400 opacity-60"
                    style={{ left: `${threshold * 100}%` }}
                  />
                </div>

                {/* Score badge */}
                <span
                  className={`text-xs font-bold px-2 py-0.5 rounded w-16 text-center ${textClass}`}
                >
                  {val.toFixed(3)}
                </span>
              </div>
            );
          })}

          {/* Legend */}
          <div className="flex items-center gap-4 pt-2 border-t border-gray-100 text-xs text-gray-500">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span>Low ≤ 0.25</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-amber-500" />
              <span>Medium ≤ 0.50</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span>High &gt; 0.50</span>
            </div>
            <div className="flex items-center gap-1 ml-auto">
              <div className="w-0.5 h-3 bg-gray-400" />
              <span>Threshold ({threshold})</span>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500 px-1">
        <span>
          {composite < threshold
            ? "AI can act autonomously on this assessment"
            : "Human approval required before AI can act"}
        </span>
        <span className={`font-medium ${status.textColor}`}>
          {status.text}
        </span>
      </div>
    </div>
  );
}
