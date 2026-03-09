"use client";

import { useEffect, useState } from "react";
import type { AudioDevice } from "@/types";
import { API_URL } from "@/lib/constants";

interface DeviceSelectorProps {
  onSelect: (deviceId: number) => void;
  selectedDeviceId: number | null;
}

export function DeviceSelector({ onSelect, selectedDeviceId }: DeviceSelectorProps) {
  const [devices, setDevices] = useState<AudioDevice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchDevices = async () => {
    setLoading(true);
    setError(false);
    try {
      const res = await fetch(`${API_URL}/devices`);
      const data = await res.json();
      setDevices(data);
    } catch {
      setDevices([]);
      setError(true);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between">
        <label className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-[0.08em]">
          P&eacute;riph&eacute;rique
        </label>
        <button
          onClick={fetchDevices}
          className="text-[11px] text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors flex items-center gap-1"
        >
          <svg viewBox="0 0 16 16" className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path d="M2.5 8a5.5 5.5 0 019.3-4M13.5 8a5.5 5.5 0 01-9.3 4" />
            <path d="M11.5 1.5v3h3M4.5 14.5v-3h-3" />
          </svg>
          Actualiser
        </button>
      </div>
      {loading ? (
        <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)]">
          <div className="w-3 h-3 border-2 border-[var(--text-muted)] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-[var(--text-muted)]">Chargement...</span>
        </div>
      ) : error ? (
        <div className="px-3 py-2.5 rounded-lg bg-red-500/5 border border-red-500/10 text-xs text-red-400/80">
          Backend non disponible
        </div>
      ) : (
        <select
          value={selectedDeviceId ?? ""}
          onChange={(e) => onSelect(Number(e.target.value))}
          className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-lg px-3 py-2.5 text-xs text-[var(--text-primary)] focus:outline-none focus:border-emerald-500/40 transition-colors"
        >
          <option value="" disabled>
            S&eacute;lectionner un p&eacute;riph&eacute;rique
          </option>
          {devices.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
