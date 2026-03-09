"use client";

import type { AudioMetrics, ListeningMode } from "@/types";
import { MODE_LABELS } from "@/lib/constants";

interface StatusBarProps {
  metrics: AudioMetrics | null;
  mode: ListeningMode;
}

interface MetricItemProps {
  label: string;
  value: string;
  unit: string;
}

function MetricItem({ label, value, unit }: MetricItemProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[var(--text-muted)]">{label}</span>
      <span className="tabular-nums text-[var(--text-primary)] min-w-[4.5ch] text-right inline-block">
        {value}
      </span>
      <span className="text-[var(--text-muted)]">{unit}</span>
    </div>
  );
}

export function StatusBar({ metrics, mode }: StatusBarProps) {
  return (
    <div className="flex items-center gap-1 px-6 py-2.5 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[11px] font-medium">
      {/* Mode indicator */}
      <div className="flex items-center gap-2 pr-4 mr-4 border-r border-[var(--border-subtle)]">
        <div className={`w-1.5 h-1.5 rounded-full ${
          mode === "cardiac" ? "bg-red-400" : mode === "respiratory" ? "bg-blue-400" : "bg-neutral-400"
        }`} />
        <span className="text-[var(--text-secondary)]">{MODE_LABELS[mode]}</span>
      </div>

      {/* Metrics — fixed width with tabular nums */}
      {metrics ? (
        <div className="flex items-center gap-6">
          <MetricItem label="RMS" value={metrics.rms_db.toFixed(1)} unit="dB" />
          <MetricItem label="Peak" value={metrics.peak_db.toFixed(1)} unit="dB" />
          <MetricItem label="SNR" value={metrics.snr.toFixed(1)} unit="dB" />
          <MetricItem label="Freq" value={metrics.dominant_freq.toFixed(0)} unit="Hz" />
        </div>
      ) : (
        <span className="text-[var(--text-muted)]">En attente de signal...</span>
      )}
    </div>
  );
}
