"use client";

import { useAudioPlayback } from "@/hooks/use-audio-playback";
import { useEffect } from "react";

interface AudioPlayerProps {
  isCapturing: boolean;
  onReady: (feedAudio: (pcm: Float32Array) => void) => void;
}

export function AudioPlayer({ isCapturing, onReady }: AudioPlayerProps) {
  const { isPlaying, start, stop, feedAudio } = useAudioPlayback();

  useEffect(() => {
    if (isCapturing && !isPlaying) {
      start().then(() => onReady(feedAudio));
    } else if (!isCapturing && isPlaying) {
      stop();
    }
  }, [isCapturing, isPlaying, start, stop, feedAudio, onReady]);

  return null; // invisible component — just manages audio context
}
