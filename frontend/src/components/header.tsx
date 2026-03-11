"use client";

import type { ConnectionStatus } from "@/types";

const STATUS_CONFIG: Record<ConnectionStatus, { label: string; color: string; ring: string }> = {
  disconnected: { label: "Hors ligne", color: "bg-neutral-500", ring: "" },
  connecting: { label: "Connexion", color: "bg-amber-400 animate-pulse", ring: "ring-1 ring-amber-400/30" },
  connected: { label: "Connect\u00e9", color: "bg-emerald-400", ring: "ring-1 ring-emerald-400/20" },
  error: { label: "Erreur", color: "bg-red-400", ring: "ring-1 ring-red-400/30" },
};

interface HeaderProps {
  connectionStatus: ConnectionStatus;
  isCapturing: boolean;
}

export function Header({ connectionStatus, isCapturing }: HeaderProps) {
  const status = STATUS_CONFIG[connectionStatus];

  return (
    <header className="flex items-center justify-between px-6 py-3.5 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]">
      <div className="flex items-center gap-4">
        {/* Logo */}
        <div className="relative">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border border-emerald-500/20 flex items-center justify-center">
            <svg viewBox="0 0 32 32" className="w-[20px] h-[20px]" fill="none">
              {/* Audio waveform bars */}
              <rect x="2" y="12" width="2.5" height="8" rx="1.25" fill="url(#waveGrad)" opacity="0.7" />
              <rect x="7" y="8" width="2.5" height="16" rx="1.25" fill="url(#waveGrad)" opacity="0.85" />
              <rect x="12" y="4" width="2.5" height="24" rx="1.25" fill="url(#waveGrad)" />
              <rect x="17" y="6" width="2.5" height="20" rx="1.25" fill="url(#waveGrad)" opacity="0.9" />
              <rect x="22" y="10" width="2.5" height="12" rx="1.25" fill="url(#waveGrad)" opacity="0.75" />
              <rect x="27" y="13" width="2.5" height="6" rx="1.25" fill="url(#waveGrad)" opacity="0.55" />
              <defs>
                <linearGradient id="waveGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#34d399" />
                  <stop offset="100%" stopColor="#059669" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          {isCapturing && (
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-red-500 animate-recording ring-2 ring-[var(--bg-surface)]" />
          )}
        </div>

        {/* Title */}
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <h1 className="text-[15px] font-semibold text-white tracking-tight leading-none">
              St&eacute;thoscope TESSAN
            </h1>
          </div>
          <span className="text-[11px] text-[var(--text-muted)] leading-none mt-1">
            Auscultation temps r&eacute;el
          </span>
        </div>
      </div>

      {/* Connection status */}
      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--bg-elevated)] ${status.ring}`}>
        <div className={`w-1.5 h-1.5 rounded-full ${status.color}`} />
        <span className="text-[11px] text-[var(--text-secondary)] font-medium">
          {status.label}
        </span>
      </div>
    </header>
  );
}
