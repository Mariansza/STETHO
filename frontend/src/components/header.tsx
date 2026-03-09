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
            <svg viewBox="0 0 24 24" className="w-[18px] h-[18px] text-emerald-400" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round">
              <path d="M12 3c-1.5 0-4 1-4 4v2c0 1.5.5 2 2 2h4c1.5 0 2-.5 2-2V7c0-3-2.5-4-4-4z" />
              <path d="M8 9l-2 1.5c-1 .8-1.5 2-1.5 3.2 0 2 1.5 3.3 3.5 3.3" />
              <path d="M16 9l2 1.5c1 .8 1.5 2 1.5 3.2 0 2-1.5 3.3-3.5 3.3" />
              <path d="M10 17v3.5a1.5 1.5 0 003 0V17" />
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
