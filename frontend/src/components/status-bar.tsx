"use client";

import type { AudioMetrics, ListeningMode } from "@/types";
import { MODE_LABELS } from "@/lib/constants";

interface StatusBarProps {
  metrics: AudioMetrics | null;
  mode: ListeningMode;
}

export function StatusBar({ metrics, mode }: StatusBarProps) {
  return (
    <div className="flex items-center gap-6 px-6 py-3 border-t border-neutral-800 text-xs text-neutral-400">
      <span>
        Mode : <span className="text-neutral-200">{MODE_LABELS[mode]}</span>
      </span>
      {metrics && (
        <>
          <span>
            RMS : <span className="text-neutral-200">{metrics.rms_db} dB</span>
          </span>
          <span>
            Peak : <span className="text-neutral-200">{metrics.peak_db} dB</span>
          </span>
          <span>
            SNR : <span className="text-neutral-200">{metrics.snr} dB</span>
          </span>
          <span>
            Freq. dom. : <span className="text-neutral-200">{metrics.dominant_freq} Hz</span>
          </span>
        </>
      )}
    </div>
  );
}
