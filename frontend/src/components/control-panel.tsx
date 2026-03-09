"use client";

import { useState } from "react";
import type { ListeningMode, ClientMessage } from "@/types";
import { MODE_LABELS, MODE_COLORS } from "@/lib/constants";

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
        className={`w-full py-3 rounded-xl font-medium text-sm transition-all ${
          isCapturing
            ? "bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30"
            : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30"
        }`}
      >
        {isCapturing ? "Arrêter la capture" : "Démarrer la capture"}
      </button>

      {/* Mode selection */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">
          Mode d&apos;écoute
        </label>
        <div className="grid grid-cols-3 gap-2">
          {modes.map((m) => (
            <button
              key={m}
              onClick={() => onSend({ type: "set_mode", mode: m })}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-all border ${
                mode === m
                  ? "border-current text-white"
                  : "border-neutral-700 text-neutral-400 hover:text-neutral-200 hover:border-neutral-600"
              }`}
              style={mode === m ? { borderColor: MODE_COLORS[m], color: MODE_COLORS[m] } : {}}
            >
              {MODE_LABELS[m]}
            </button>
          ))}
        </div>
      </div>

      {/* Gain slider */}
      <div className="space-y-2">
        <div className="flex justify-between">
          <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">
            Gain
          </label>
          <span className="text-xs text-neutral-500">{gain.toFixed(1)}x</span>
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
          className="w-full accent-emerald-500"
        />
      </div>

      {/* Noise reduction */}
      <div className="space-y-2">
        <div className="flex justify-between">
          <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">
            Réduction bruit
          </label>
          <span className="text-xs text-neutral-500">{noiseAlpha.toFixed(1)}</span>
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
          className="w-full accent-emerald-500"
        />
        <button
          onClick={() => onSend({ type: "recalibrate_noise" })}
          className="w-full py-2 rounded-lg text-xs font-medium bg-neutral-800 border border-neutral-700 text-neutral-400 hover:text-neutral-200 hover:border-neutral-600 transition-all"
        >
          Recalibrer le bruit ambiant
        </button>
      </div>
    </div>
  );
}
