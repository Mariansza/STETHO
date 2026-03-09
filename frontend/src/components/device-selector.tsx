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

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/devices`);
      const data = await res.json();
      setDevices(data);
    } catch {
      setDevices([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">
          Périphérique audio
        </label>
        <button
          onClick={fetchDevices}
          className="text-xs text-neutral-500 hover:text-neutral-300 transition-colors"
        >
          Rafraîchir
        </button>
      </div>
      {loading ? (
        <div className="text-sm text-neutral-500">Chargement…</div>
      ) : (
        <select
          value={selectedDeviceId ?? ""}
          onChange={(e) => onSelect(Number(e.target.value))}
          className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-emerald-500"
        >
          <option value="" disabled>
            Sélectionner un périphérique
          </option>
          {devices.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} ({d.hostapi})
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
