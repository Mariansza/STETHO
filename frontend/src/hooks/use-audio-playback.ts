"use client";

import { useCallback, useRef, useState } from "react";
import { SAMPLE_RATE } from "@/lib/constants";

export function useAudioPlayback() {
  const [isPlaying, setIsPlaying] = useState(false);
  const ctxRef = useRef<AudioContext | null>(null);
  const workletRef = useRef<AudioWorkletNode | null>(null);

  const start = useCallback(async () => {
    if (ctxRef.current) return;

    const ctx = new AudioContext({ sampleRate: SAMPLE_RATE });
    await ctx.audioWorklet.addModule("/worklets/pcm-playback-processor.js");
    const worklet = new AudioWorkletNode(ctx, "pcm-playback-processor");
    worklet.connect(ctx.destination);

    ctxRef.current = ctx;
    workletRef.current = worklet;
    setIsPlaying(true);
  }, []);

  const stop = useCallback(() => {
    workletRef.current?.disconnect();
    workletRef.current = null;
    ctxRef.current?.close();
    ctxRef.current = null;
    setIsPlaying(false);
  }, []);

  const feedAudio = useCallback((pcm: Float32Array) => {
    workletRef.current?.port.postMessage(pcm);
  }, []);

  return { isPlaying, start, stop, feedAudio };
}
