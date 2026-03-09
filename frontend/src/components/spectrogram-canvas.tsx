"use client";

import { useEffect, useRef } from "react";

interface SpectrogramCanvasProps {
  row: number[] | null;
  height?: number;
}

// Color map: deep blue → teal → green → yellow → orange → red/white
function dbToRGB(db: number): [number, number, number] {
  const t = Math.max(0, Math.min(1, (db + 80) / 65));

  if (t < 0.2) {
    const s = t / 0.2;
    return [0, Math.floor(s * 40), Math.floor(20 + s * 80)];
  } else if (t < 0.4) {
    const s = (t - 0.2) / 0.2;
    return [0, Math.floor(40 + s * 120), Math.floor(100 + s * 80)];
  } else if (t < 0.6) {
    const s = (t - 0.4) / 0.2;
    return [Math.floor(s * 80), Math.floor(160 + s * 60), Math.floor(180 - s * 100)];
  } else if (t < 0.8) {
    const s = (t - 0.6) / 0.2;
    return [Math.floor(80 + s * 175), Math.floor(220 - s * 60), Math.floor(80 - s * 60)];
  } else {
    const s = (t - 0.8) / 0.2;
    return [255, Math.floor(160 + s * 95), Math.floor(20 + s * 100)];
  }
}

export function SpectrogramCanvas({ row, height = 220 }: SpectrogramCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const bufferRef = useRef<ImageData | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !row || row.length === 0) return;

    const ctx = canvas.getContext("2d", { alpha: false });
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const w = Math.floor(rect.width);
    const h = Math.floor(rect.height);

    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
      bufferRef.current = null;
    }

    // Shift image left by 2px
    if (bufferRef.current) {
      ctx.putImageData(bufferRef.current, -2, 0);
    }

    // Draw new column(s) on right edge
    const colWidth = 2;
    const binH = h / row.length;

    for (let i = 0; i < row.length; i++) {
      const y = h - (i + 1) * binH;
      const [r, g, b] = dbToRGB(row[i]);
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(w - colWidth, y, colWidth, Math.ceil(binH) + 1);
    }

    bufferRef.current = ctx.getImageData(0, 0, w, h);
  }, [row]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-[0.08em]">
          Spectrogramme
        </label>
        <div className="flex items-center gap-3 text-[10px] text-[var(--text-muted)]">
          <span>Basses freq.</span>
          <div className="w-16 h-1.5 rounded-full" style={{
            background: "linear-gradient(90deg, #001450, #00a0b4, #50dc50, #ffb414, #ff6428, #fff078)"
          }} />
          <span>Hautes freq.</span>
        </div>
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
