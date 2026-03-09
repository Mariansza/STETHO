"use client";

import { useEffect, useRef } from "react";

interface WaveformCanvasProps {
  samples: Float32Array | null;
  color?: string;
  height?: number;
}

export function WaveformCanvas({
  samples,
  color = "#34d399",
  height = 160,
}: WaveformCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !samples || samples.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const mid = h / 2;

    // Background
    ctx.fillStyle = "#0c0c12";
    ctx.fillRect(0, 0, w, h);

    // Subtle grid
    ctx.strokeStyle = "#1a1a24";
    ctx.lineWidth = 0.5;
    for (let i = 1; i < 4; i++) {
      const y = (h / 4) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Center line (brighter)
    ctx.strokeStyle = "#252530";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, mid);
    ctx.lineTo(w, mid);
    ctx.stroke();

    // Waveform fill gradient
    const gradient = ctx.createLinearGradient(0, mid - h * 0.4, 0, mid + h * 0.4);
    gradient.addColorStop(0, color + "18");
    gradient.addColorStop(0.5, color + "05");
    gradient.addColorStop(1, color + "18");

    // Draw filled area
    ctx.beginPath();
    const step = w / samples.length;
    ctx.moveTo(0, mid);
    for (let i = 0; i < samples.length; i++) {
      const x = i * step;
      const y = mid - samples[i] * mid * 0.85;
      ctx.lineTo(x, y);
    }
    ctx.lineTo(w, mid);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw waveform line
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.lineJoin = "round";

    for (let i = 0; i < samples.length; i++) {
      const x = i * step;
      const y = mid - samples[i] * mid * 0.85;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Glow effect on the line
    ctx.strokeStyle = color + "40";
    ctx.lineWidth = 4;
    ctx.stroke();
  }, [samples, color]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-[0.08em]">
          Forme d&apos;onde
        </label>
        <span className="text-[10px] text-[var(--text-muted)]">Temps r&eacute;el</span>
      </div>
      <div className="canvas-container rounded-xl overflow-hidden">
        <canvas
          ref={canvasRef}
          style={{ height }}
          className="w-full bg-[#0c0c12] block"
        />
      </div>
    </div>
  );
}
