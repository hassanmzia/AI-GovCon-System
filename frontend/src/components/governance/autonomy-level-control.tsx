"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, CheckCircle, Shield, Zap } from "lucide-react";

interface AutonomyLevelControlProps {
  currentLevel: 0 | 1 | 2 | 3;
  killSwitchActive: boolean;
  onLevelChange?: (level: number) => void;
  onKillSwitch?: () => void;
  readOnly?: boolean;
}

const LEVELS = [
  {
    id: 0,
    label: "L0",
    name: "Assistive",
    shortName: "L0 Assistive",
    description:
      "AI drafts & recommends. Human executes everything. Use for high-risk or classified work.",
    colorKey: "slate",
    activeBorder: "border-slate-500",
    activeBg: "bg-slate-50",
    activeText: "text-slate-700",
    inactiveBorder: "border-gray-200",
    inactiveBg: "bg-white",
    badgeBg: "bg-slate-100",
    badgeText: "text-slate-600",
    dotColor: "bg-slate-400",
  },
  {
    id: 1,
    label: "L1",
    name: "Guided",
    shortName: "L1 Guided (Default)",
    description:
      "AI prepares full packages. Human approves and clicks submit. Default recommended.",
    colorKey: "blue",
    activeBorder: "border-blue-500",
    activeBg: "bg-blue-50",
    activeText: "text-blue-700",
    inactiveBorder: "border-gray-200",
    inactiveBg: "bg-white",
    badgeBg: "bg-blue-100",
    badgeText: "text-blue-600",
    dotColor: "bg-blue-500",
  },
  {
    id: 2,
    label: "L2",
    name: "Conditional",
    shortName: "L2 Conditional",
    description:
      "AI can auto-advance stages and send pre-approved templates. Pricing/submission still HITL.",
    colorKey: "amber",
    activeBorder: "border-amber-500",
    activeBg: "bg-amber-50",
    activeText: "text-amber-700",
    inactiveBorder: "border-gray-200",
    inactiveBg: "bg-white",
    badgeBg: "bg-amber-100",
    badgeText: "text-amber-600",
    dotColor: "bg-amber-500",
  },
  {
    id: 3,
    label: "L3",
    name: "Strategic",
    shortName: "L3 Strategic",
    description:
      "AI can auto-bid under preset thresholds. Requires confidence + risk gates to pass.",
    colorKey: "red",
    activeBorder: "border-red-500",
    activeBg: "bg-red-50",
    activeText: "text-red-700",
    inactiveBorder: "border-gray-200",
    inactiveBg: "bg-white",
    badgeBg: "bg-red-100",
    badgeText: "text-red-600",
    dotColor: "bg-red-500",
  },
] as const;

export function AutonomyLevelControl({
  currentLevel,
  killSwitchActive,
  onLevelChange,
  onKillSwitch,
  readOnly = false,
}: AutonomyLevelControlProps) {
  return (
    <div className="space-y-4">
      {/* Kill Switch Banner or Button */}
      {killSwitchActive ? (
        <div className="rounded-lg border-2 border-orange-400 bg-orange-50 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-orange-600 flex-shrink-0" />
            <div>
              <p className="font-bold text-orange-800 text-lg">
                KILL SWITCH ACTIVE
              </p>
              <p className="text-orange-700 text-sm">
                All AI autonomous actions are frozen. The system is operating in
                full human-oversight mode.
              </p>
            </div>
          </div>
          {!readOnly && onKillSwitch && (
            <Button
              onClick={onKillSwitch}
              className="bg-orange-600 hover:bg-orange-700 text-white font-bold px-6 whitespace-nowrap ml-4"
            >
              Click to Restore L1
            </Button>
          )}
        </div>
      ) : (
        !readOnly &&
        onKillSwitch && (
          <button
            onClick={onKillSwitch}
            className="w-full rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold py-4 px-6 text-lg flex items-center justify-center gap-3 transition-colors shadow-md"
          >
            <Zap className="h-6 w-6" />
            KILL SWITCH — Freeze All AI Actions
          </button>
        )
      )}

      {/* Level Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {LEVELS.map((level) => {
          const isActive = currentLevel === level.id;
          const isClickable = !readOnly && !killSwitchActive && onLevelChange;

          return (
            <div
              key={level.id}
              onClick={isClickable ? () => onLevelChange(level.id) : undefined}
              className={[
                "rounded-lg border-2 p-4 transition-all",
                isActive ? level.activeBorder : level.inactiveBorder,
                isActive ? level.activeBg : level.inactiveBg,
                isClickable
                  ? "cursor-pointer hover:shadow-md hover:scale-[1.01]"
                  : "cursor-default",
                killSwitchActive ? "opacity-50" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {/* Header row */}
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`text-xs font-bold px-2 py-0.5 rounded ${level.badgeBg} ${level.badgeText}`}
                >
                  {level.label}
                </span>
                {isActive && !killSwitchActive && (
                  <CheckCircle
                    className={`h-4 w-4 ${level.activeText}`}
                  />
                )}
              </div>

              {/* Level name */}
              <p
                className={`font-semibold text-sm mb-1 ${
                  isActive ? level.activeText : "text-gray-700"
                }`}
              >
                {level.name}
                {level.id === 1 && (
                  <span className="ml-1 text-xs font-normal text-gray-500">
                    (Default)
                  </span>
                )}
              </p>

              {/* Description */}
              <p className="text-xs text-gray-500 leading-relaxed">
                {level.description}
              </p>

              {/* Active dot indicator */}
              {isActive && (
                <div className="mt-3 flex items-center gap-1.5">
                  <div
                    className={`w-2 h-2 rounded-full ${level.dotColor} animate-pulse`}
                  />
                  <span className={`text-xs font-medium ${level.activeText}`}>
                    Active
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer info */}
      <div className="flex items-center gap-2 text-xs text-gray-500 px-1">
        <Shield className="h-3.5 w-3.5" />
        <span>
          {killSwitchActive
            ? "Kill switch active — all autonomous AI actions are suspended."
            : currentLevel === 0
            ? "L0: Full human control. AI assists only."
            : currentLevel === 1
            ? "L1: AI prepares, human approves. Recommended for most operations."
            : currentLevel === 2
            ? "L2: Conditional autonomy. Pricing and submissions still require human approval."
            : "L3: High autonomy. Strict confidence and risk gates enforced."}
        </span>
      </div>
    </div>
  );
}
