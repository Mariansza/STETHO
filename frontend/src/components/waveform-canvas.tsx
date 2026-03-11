"use client";

import { useEffect, useRef } from "react";
import { SAMPLE_RATE } from "@/lib/constants";

interface WaveformCanvasProps {
  samples: Float32Array | null;
  color?: string;
  height?: number;
  /** Duration of visible window in seconds */
  duration?: number;
}

// ~3 seconds at 44100 Hz
const DEFAULT_DURATION = 3;

export function WaveformCanvas({
  samples,
  color = "#34d399",
  height = 200,
  duration = DEFAULT_DURATION,
}: WaveformCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const bufferRef = useRef<Float32Array>(new Float32Array(0));
  const maxSamplesRef = useRef(SAMPLE_RATE * duration);

  // Update max samples if duration changes
  maxSamplesRef.current = SAMPLE_RATE * duration;

  useEffect(() => {
    if (!samples || samples.length === 0) return;

    // Append new samples to the rolling buffer
    const maxLen = maxSamplesRef.current;
    const prev = bufferRef.current;
    const totalLen = prev.length + samples.length;

    if (totalLen <= maxLen) {
      const newBuf = new Float32Array(totalLen);
      newBuf.set(prev, 0);
      newBuf.set(samples, prev.length);
      bufferRef.current = newBuf;
    } else {
      // Trim from the front to keep maxLen samples
      const newBuf = new Float32Array(maxLen);
      const keep = maxLen - samples.length;
      if (keep > 0) {
        newBuf.set(prev.subarray(prev.length - keep), 0);
        newBuf.set(samples, keep);
      } else {
        newBuf.set(samples.subarray(samples.length - maxLen), 0);
      }
      bufferRef.current = newBuf;
    }

    // Draw
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const padBottom = 20;
    const plotH = h - padBottom;
    const mid = plotH / 2;

    const buf = bufferRef.current;

    // Background
    ctx.fillStyle = "#0c0c12";
    ctx.fillRect(0, 0, w, h);

    // Horizontal grid lines (amplitude)
    ctx.strokeStyle = "#1a1a24";
    ctx.lineWidth = 0.5;
    for (let i = 1; i < 4; i++) {
      const y = (plotH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Center line
    ctx.strokeStyle = "#252530";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, mid);
    ctx.lineTo(w, mid);
    ctx.stroke();

    // Time markers
    ctx.fillStyle = "#3a3a4a";
    ctx.font = "9px ui-monospace, monospace";
    ctx.textAlign = "center";

    const totalDuration = buf.length / SAMPLE_RATE;
    const step1s = w / totalDuration; // pixels per second
    for (let t = 1; t <= Math.floor(totalDuration); t++) {
      const x = w - (totalDuration - t) * step1s;
      if (x < 20 || x > w - 20) continue;

      // Vertical tick
      ctx.strokeStyle = "#1a1a24";
      ctx.lineWidth = 0.5;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, plotH);
      ctx.stroke();

      ctx.fillText(`${t}s`, x, h - 5);
    }

    if (buf.length < 2) return;

    // Downsample for drawing: we don't need more points than pixels
    // Use min/max per pixel column for accurate representation
    const samplesPerPixel = buf.length / w;

    // Fill gradient under curve
    const gradient = ctx.createLinearGradient(0, mid - plotH * 0.4, 0, mid + plotH * 0.4);
    gradient.addColorStop(0, color + "15");
    gradient.addColorStop(0.5, color + "03");
    gradient.addColorStop(1, color + "15");

    // Draw min/max envelope as filled area
    ctx.beginPath();
    ctx.moveTo(0, mid);

    // Top edge (max values)
    const mins: number[] = [];
    for (let px = 0; px < w; px++) {
      const startIdx = Math.floor(px * samplesPerPixel);
      const endIdx = Math.min(Math.floor((px + 1) * samplesPerPixel), buf.length);
      let maxVal = -1;
      let minVal = 1;
      for (let j = startIdx; j < endIdx; j++) {
        if (buf[j] > maxVal) maxVal = buf[j];
        if (buf[j] < minVal) minVal = buf[j];
      }
      const yMax = mid - maxVal * mid * 0.88;
      ctx.lineTo(px, yMax);
      mins.push(minVal);
    }

    // Bottom edge (min values, reversed)
    for (let px = w - 1; px >= 0; px--) {
      const yMin = mid - mins[px] * mid * 0.88;
      ctx.lineTo(px, yMin);
    }

    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw center line of waveform (average of min/max per pixel)
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.2;
    ctx.lineJoin = "round";

    for (let px = 0; px < w; px++) {
      const startIdx = Math.floor(px * samplesPerPixel);
      const endIdx = Math.min(Math.floor((px + 1) * samplesPerPixel), buf.length);
      let maxVal = -1;
      let minVal = 1;
      for (let j = startIdx; j < endIdx; j++) {
        if (buf[j] > maxVal) maxVal = buf[j];
        if (buf[j] < minVal) minVal = buf[j];
      }
      const yMid = mid - ((maxVal + minVal) / 2) * mid * 0.88;
      if (px === 0) ctx.moveTo(px, yMid);
      else ctx.lineTo(px, yMid);
    }
    ctx.stroke();

    // Glow on the line
    ctx.strokeStyle = color + "25";
    ctx.lineWidth = 3;
    ctx.stroke();

    // Playhead line at the right edge
    ctx.strokeStyle = color + "60";
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(w - 1, 0);
    ctx.lineTo(w - 1, plotH);
    ctx.stroke();
    ctx.setLineDash([]);

  }, [samples, color, duration]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-[0.08em]">
          Forme d&apos;onde
        </label>
        <span className="text-[10px] text-[var(--text-muted)]">
          {duration}s &bull; Temps r&eacute;el
        </span>
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
