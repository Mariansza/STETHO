"use client";

import type { ConnectionStatus } from "@/types";

const STATUS_LABEL: Record<ConnectionStatus, string> = {
  disconnected: "Déconnecté",
  connecting: "Connexion…",
  connected: "Connecté",
  error: "Erreur",
};

const STATUS_COLOR: Record<ConnectionStatus, string> = {
  disconnected: "bg-neutral-500",
  connecting: "bg-yellow-500 animate-pulse",
  connected: "bg-emerald-500",
  error: "bg-red-500",
};

interface HeaderProps {
  connectionStatus: ConnectionStatus;
}

export function Header({ connectionStatus }: HeaderProps) {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-neutral-800">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
          <svg
            viewBox="0 0 24 24"
            className="w-5 h-5 text-white"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path d="M4.5 12.5c0-2.5 2-4 4-4s4 1.5 4 4-2 4-4 4-4-1.5-4-4z" />
            <path d="M12.5 12.5c0-2.5 2-4 4-4s4 1.5 4 4-2 4-4 4-4-1.5-4-4z" />
            <path d="M8.5 16.5V20a1 1 0 002 0v-3.5" />
            <path d="M16.5 16.5V20a1 1 0 01-2 0v-3.5" />
          </svg>
        </div>
        <h1 className="text-xl font-semibold text-white tracking-tight">
          Stetho
        </h1>
        <span className="text-xs text-neutral-500 mt-1">
          Auscultation temps réel
        </span>
      </div>
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${STATUS_COLOR[connectionStatus]}`} />
        <span className="text-sm text-neutral-400">
          {STATUS_LABEL[connectionStatus]}
        </span>
      </div>
    </header>
  );
}
