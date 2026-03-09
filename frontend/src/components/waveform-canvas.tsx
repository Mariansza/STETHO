"use client";

import { useEffect, useRef } from "react";

interface WaveformCanvasProps {
  samples: Float32Array | null;
  color?: string;
  height?: number;
}

export function WaveformCanvas({
  samples,
  color = "#22c55e",
  height = 150,
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

    // Background
    ctx.fillStyle = "#0a0a0a";
    ctx.fillRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = "#1a1a1a";
    ctx.lineWidth = 1;
    const mid = h / 2;
    ctx.beginPath();
    ctx.moveTo(0, mid);
    ctx.lineTo(w, mid);
    ctx.stroke();

    // Waveform
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;

    const step = w / samples.length;
    for (let i = 0; i < samples.length; i++) {
      const x = i * step;
      const y = mid - samples[i] * mid * 0.85;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }, [samples, color]);

  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">
        Forme d&apos;onde
      </label>
      <canvas
        ref={canvasRef}
        style={{ height }}
        className="w-full rounded-lg border border-neutral-800 bg-[#0a0a0a]"
      />
    </div>
  );
}
