"use client";

import { useCallback, useRef, useState } from "react";

/**
 * Gapless audio playback by batching PCM chunks before scheduling.
 *
 * Accumulates BATCH_SIZE chunks into a single AudioBufferSourceNode
 * to minimize the number of buffer boundaries. Fewer boundaries = fewer
 * opportunities for micro-gaps that are audible on narrow-band audio.
 */
const BATCH_SIZE = 4; // accumulate 4 chunks (~93ms @ 1024/44100) before playing

export function useAudioPlayback() {
  const [isPlaying, setIsPlaying] = useState(false);
  const ctxRef = useRef<AudioContext | null>(null);
  const sampleRateRef = useRef<number>(44100);
  const nextTimeRef = useRef<number>(0);
  const accumulatorRef = useRef<Float32Array[]>([]);

  const start = useCallback(async (sampleRate?: number) => {
    if (ctxRef.current) {
      if (sampleRate && sampleRate !== sampleRateRef.current) {
        await ctxRef.current.close();
        ctxRef.current = null;
      } else {
        return;
      }
    }

    const sr = sampleRate ?? sampleRateRef.current;
    sampleRateRef.current = sr;

    const ctx = new AudioContext({ sampleRate: sr });
    ctxRef.current = ctx;
    nextTimeRef.current = 0;
    accumulatorRef.current = [];
    setIsPlaying(true);
  }, []);

  const stop = useCallback(() => {
    ctxRef.current?.close();
    ctxRef.current = null;
    nextTimeRef.current = 0;
    accumulatorRef.current = [];
    setIsPlaying(false);
  }, []);

  const scheduleBatch = useCallback((ctx: AudioContext, chunks: Float32Array[]) => {
    // Merge all chunks into a single buffer
    const totalLength = chunks.reduce((sum, c) => sum + c.length, 0);
    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }

    const buffer = ctx.createBuffer(1, totalLength, ctx.sampleRate);
    buffer.getChannelData(0).set(merged);

    const source = new AudioBufferSourceNode(ctx);
    source.buffer = buffer;
    source.connect(ctx.destination);

    const now = ctx.currentTime;
    if (nextTimeRef.current <= now) {
      nextTimeRef.current = now + 0.1; // 100ms head start for jitter absorption
    }

    source.start(nextTimeRef.current);
    nextTimeRef.current += totalLength / ctx.sampleRate;
  }, []);

  const feedAudio = useCallback((pcm: Float32Array) => {
    const ctx = ctxRef.current;
    if (!ctx || ctx.state === "closed") return;

    if (ctx.state === "suspended") {
      ctx.resume();
    }

    // Accumulate chunks
    accumulatorRef.current.push(new Float32Array(pcm));

    if (accumulatorRef.current.length >= BATCH_SIZE) {
      scheduleBatch(ctx, accumulatorRef.current);
      accumulatorRef.current = [];
    }
  }, [scheduleBatch]);

  return { isPlaying, start, stop, feedAudio };
}
