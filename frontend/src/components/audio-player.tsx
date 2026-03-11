"use client";

import { useAudioPlayback } from "@/hooks/use-audio-playback";
import { useEffect, useRef } from "react";

interface AudioPlayerProps {
  isCapturing: boolean;
  sampleRate: number;
  onReady: (feedAudio: (pcm: Float32Array) => void) => void;
}

export function AudioPlayer({ isCapturing, sampleRate, onReady }: AudioPlayerProps) {
  const { isPlaying, start, stop, feedAudio } = useAudioPlayback();
  const prevCapturing = useRef(false);

  useEffect(() => {
    if (isCapturing && !prevCapturing.current) {
      start(sampleRate).then(() => onReady(feedAudio));
    } else if (!isCapturing && prevCapturing.current) {
      stop();
    } else if (isCapturing && isPlaying && sampleRate) {
      // Sample rate changed while capturing — restart audio context
      start(sampleRate).then(() => onReady(feedAudio));
    }
    prevCapturing.current = isCapturing;
  }, [isCapturing, sampleRate, isPlaying, start, stop, feedAudio, onReady]);

  return null;
}
