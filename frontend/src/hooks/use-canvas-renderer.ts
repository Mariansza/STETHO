"use client";

import { useCallback, useRef } from "react";

export function useCanvasRenderer(
  canvasRef: React.RefObject<HTMLCanvasElement | null>,
) {
  const animFrameRef = useRef<number>(0);

  const getCtx = useCallback(() => {
    return canvasRef.current?.getContext("2d") ?? null;
  }, [canvasRef]);

  const clear = useCallback(
    (color = "#0a0a0a") => {
      const ctx = getCtx();
      if (!ctx) return;
      const { width, height } = ctx.canvas;
      ctx.fillStyle = color;
      ctx.fillRect(0, 0, width, height);
    },
    [getCtx],
  );

  const drawWaveform = useCallback(
    (
      samples: Float32Array,
      color = "#22c55e",
    ) => {
      const ctx = getCtx();
      if (!ctx) return;
      const { width, height } = ctx.canvas;

      ctx.fillStyle = "#0a0a0a";
      ctx.fillRect(0, 0, width, height);

      ctx.beginPath();
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;

      const mid = height / 2;
      const step = width / samples.length;

      for (let i = 0; i < samples.length; i++) {
        const x = i * step;
        const y = mid - samples[i] * mid * 0.9;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    },
    [getCtx],
  );

  return { getCtx, clear, drawWaveform, animFrameRef };
}
