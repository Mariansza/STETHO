"use client";

import { useState } from "react";
import type { ListeningMode, ClientMessage } from "@/types";
import { MODE_LABELS } from "@/lib/constants";

const MODE_CONFIG: Record<ListeningMode, { color: string; bg: string; border: string; icon: string }> = {
  cardiac: {
    color: "text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    icon: "M3.5 12l3-3 2.5 5 3-7 2.5 5 3-3",
  },
  respiratory: {
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    icon: "M3 12c2-3 4-3 5 0s3 3 5 0 3-3 5 0",
  },
  raw: {
    color: "text-neutral-400",
    bg: "bg-neutral-500/10",
    border: "border-neutral-500/30",
    icon: "M3 12h18",
  },
};

interface ControlPanelProps {
  mode: ListeningMode;
  isCapturing: boolean;
  onSend: (msg: ClientMessage) => void;
  onStartCapture: () => void;
  onStopCapture: () => void;
}

export function ControlPanel({
  mode,
  isCapturing,
  onSend,
  onStartCapture,
  onStopCapture,
}: ControlPanelProps) {
  const [gain, setGain] = useState(1.0);
  const [noiseAlpha, setNoiseAlpha] = useState(2.0);

  const modes: ListeningMode[] = ["cardiac", "respiratory", "raw"];

  return (
    <div className="space-y-5">
      {/* Capture button */}
      <button
        onClick={isCapturing ? onStopCapture : onStartCapture}
        className={`group relative w-full py-3 rounded-xl font-medium text-sm transition-all duration-200 overflow-hidden ${
          isCapturing
            ? "bg-red-500/8 text-red-400 border border-red-500/20 hover:border-red-500/40 glow-red"
            : "bg-emerald-500/8 text-emerald-400 border border-emerald-500/20 hover:border-emerald-500/40 glow-emerald"
        }`}
      >
        <span className="relative z-10 flex items-center justify-center gap-2">
          {isCapturing ? (
            <>
              <span className="w-2.5 h-2.5 rounded-sm bg-red-400" />
              Arr&ecirc;ter la capture
            </>
          ) : (
            <>
              <svg viewBox="0 0 16 16" className="w-4 h-4" fill="currentColor">
                <path d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM6.5 5.5l5 2.5-5 2.5v-5z" />
              </svg>
              D&eacute;marrer la capture
            </>
          )}
        </span>
      </button>

      {/* Separator */}
      <div className="h-px bg-[var(--border-subtle)]" />

      {/* Mode selection */}
      <div className="space-y-2.5">
        <label className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-[0.08em]">
          Mode d&apos;&eacute;coute
        </label>
        <div className="space-y-1.5">
          {modes.map((m) => {
            const cfg = MODE_CONFIG[m];
            const active = mode === m;
            return (
              <button
                key={m}
                onClick={() => onSend({ type: "set_mode", mode: m })}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 border ${
                  active
                    ? `${cfg.bg} ${cfg.border} ${cfg.color}`
                    : "border-transparent text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)]"
                }`}
              >
                <svg viewBox="0 0 20 16" className="w-5 h-4 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
                  <path d={cfg.icon} />
                </svg>
                {MODE_LABELS[m]}
                {active && (
                  <span className={`ml-auto w-1.5 h-1.5 rounded-full ${cfg.color.replace("text-", "bg-")}`} />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Separator */}
      <div className="h-px bg-[var(--border-subtle)]" />

      {/* Gain slider */}
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <label className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-[0.08em]">
            Gain
          </label>
          <span className="tabular-nums text-[11px] text-[var(--text-secondary)] bg-[var(--bg-elevated)] px-2 py-0.5 rounded">
            {gain.toFixed(1)}x
          </span>
        </div>
        <input
          type="range"
          min="0.1"
          max="5.0"
          step="0.1"
          value={gain}
          onChange={(e) => {
            const v = parseFloat(e.target.value);
            setGain(v);
            onSend({ type: "set_params", params: { gain: v } });
          }}
          className="w-full"
        />
      </div>

      {/* Noise reduction */}
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <label className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-[0.08em]">
            R&eacute;duction bruit
          </label>
          <span className="tabular-nums text-[11px] text-[var(--text-secondary)] bg-[var(--bg-elevated)] px-2 py-0.5 rounded">
            {noiseAlpha.toFixed(1)}
          </span>
        </div>
        <input
          type="range"
          min="0.5"
          max="4.0"
          step="0.1"
          value={noiseAlpha}
          onChange={(e) => {
            const v = parseFloat(e.target.value);
            setNoiseAlpha(v);
            onSend({ type: "set_noise_reduction", alpha: v, beta: 0.02 });
          }}
          className="w-full"
        />
        <button
          onClick={() => onSend({ type: "recalibrate_noise" })}
          className="w-full py-2 rounded-lg text-[11px] font-medium bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:border-[var(--border-default)] transition-all"
        >
          Recalibrer le bruit ambiant
        </button>
      </div>
    </div>
  );
}
