"use client";

import { useEffect, useRef } from "react";

interface SpectrogramCanvasProps {
  row: number[] | null;
  height?: number;
}

// Color map: dark blue → cyan → yellow → red
function dbToColor(db: number): string {
  // Normalize: -80dB = cold, -10dB = hot
  const t = Math.max(0, Math.min(1, (db + 80) / 70));

  let r: number, g: number, b: number;
  if (t < 0.33) {
    const s = t / 0.33;
    r = 0;
    g = Math.floor(s * 180);
    b = Math.floor(60 + s * 195);
  } else if (t < 0.66) {
    const s = (t - 0.33) / 0.33;
    r = Math.floor(s * 255);
    g = Math.floor(180 + s * 75);
    b = Math.floor(255 - s * 255);
  } else {
    const s = (t - 0.66) / 0.34;
    r = 255;
    g = Math.floor(255 - s * 200);
    b = 0;
  }

  return `rgb(${r},${g},${b})`;
}

export function SpectrogramCanvas({ row, height = 200 }: SpectrogramCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageDataRef = useRef<ImageData | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !row || row.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const w = Math.floor(rect.width * dpr);
    const h = Math.floor(rect.height * dpr);

    // Initialize canvas size if needed
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
      ctx.scale(dpr, dpr);
      imageDataRef.current = null;
    }

    // Shift existing content left by 1 column (scrolling spectrogram)
    if (imageDataRef.current) {
      ctx.putImageData(imageDataRef.current, -dpr, 0);
    }

    // Draw new column on the right edge
    const displayW = rect.width;
    const displayH = rect.height;
    const colX = displayW - 1;
    const binH = displayH / row.length;

    for (let i = 0; i < row.length; i++) {
      // Spectrogram: low freq at bottom
      const y = displayH - (i + 1) * binH;
      ctx.fillStyle = dbToColor(row[i]);
      ctx.fillRect(colX, y, 2, Math.ceil(binH) + 1);
    }

    // Save for next shift
    imageDataRef.current = ctx.getImageData(0, 0, w, h);
  }, [row]);

  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-neutral-400 uppercase tracking-wider">
        Spectrogramme
      </label>
      <canvas
        ref={canvasRef}
        style={{ height }}
        className="w-full rounded-lg border border-neutral-800 bg-[#0a0a0a]"
      />
    </div>
  );
}
