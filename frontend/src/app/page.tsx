"use client";

import { useCallback, useRef, useState } from "react";
import type { AudioMetrics, ListeningMode, VizMessage } from "@/types";
import { useWebSocket } from "@/hooks/use-websocket";
import { Header } from "@/components/header";
import { DeviceSelector } from "@/components/device-selector";
import { ControlPanel } from "@/components/control-panel";
import { WaveformCanvas } from "@/components/waveform-canvas";
import { SpectrogramCanvas } from "@/components/spectrogram-canvas";
import { AudioPlayer } from "@/components/audio-player";
import { StatusBar } from "@/components/status-bar";

export default function Home() {
  const [mode, setMode] = useState<ListeningMode>("cardiac");
  const [isCapturing, setIsCapturing] = useState(false);
  const [deviceId, setDeviceId] = useState<number | null>(null);
  const [metrics, setMetrics] = useState<AudioMetrics | null>(null);
  const [waveformSamples, setWaveformSamples] = useState<Float32Array | null>(null);
  const [spectrogramRow, setSpectrogramRow] = useState<number[] | null>(null);

  const feedAudioRef = useRef<((pcm: Float32Array) => void) | null>(null);

  const onAudioFrame = useCallback((pcm: Float32Array) => {
    feedAudioRef.current?.(pcm);
    setWaveformSamples(pcm);
  }, []);

  const onVizMessage = useCallback((viz: VizMessage) => {
    setMetrics(viz.metrics);
    setSpectrogramRow(viz.spectrogram_row);
  }, []);

  const { status, connect, send } = useWebSocket({
    onAudioFrame,
    onVizMessage,
  });

  const handleSend = useCallback(
    (msg: Parameters<typeof send>[0]) => {
      if (msg.type === "set_mode") {
        setMode(msg.mode);
      }
      send(msg);
    },
    [send],
  );

  const handleStartCapture = useCallback(() => {
    if (status !== "connected") {
      connect();
      // Wait for connection then start
      const check = setInterval(() => {
        send({ type: "start_capture", device_id: deviceId ?? undefined });
        setIsCapturing(true);
        clearInterval(check);
      }, 500);
      return;
    }
    send({ type: "start_capture", device_id: deviceId ?? undefined });
    setIsCapturing(true);
  }, [status, connect, send, deviceId]);

  const handleStopCapture = useCallback(() => {
    send({ type: "stop_capture" });
    setIsCapturing(false);
  }, [send]);

  const handleDeviceSelect = useCallback(
    (id: number) => {
      setDeviceId(id);
      if (isCapturing) {
        send({ type: "set_device", device_id: id });
      }
    },
    [isCapturing, send],
  );

  const handleAudioReady = useCallback((feed: (pcm: Float32Array) => void) => {
    feedAudioRef.current = feed;
  }, []);

  return (
    <div className="h-screen flex flex-col bg-[#0a0a0a]">
      <Header connectionStatus={status} />

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside className="w-72 border-r border-neutral-800 p-5 space-y-6 overflow-y-auto">
          <DeviceSelector
            onSelect={handleDeviceSelect}
            selectedDeviceId={deviceId}
          />
          <ControlPanel
            mode={mode}
            isCapturing={isCapturing}
            onSend={handleSend}
            onStartCapture={handleStartCapture}
            onStopCapture={handleStopCapture}
          />
        </aside>

        {/* Main content */}
        <main className="flex-1 p-5 space-y-4 overflow-y-auto">
          <WaveformCanvas
            samples={waveformSamples}
            color={
              mode === "cardiac"
                ? "#ef4444"
                : mode === "respiratory"
                  ? "#3b82f6"
                  : "#a3a3a3"
            }
            height={180}
          />
          <SpectrogramCanvas row={spectrogramRow} height={250} />

          {!isCapturing && (
            <div className="flex items-center justify-center h-32 text-neutral-600 text-sm">
              Sélectionnez un périphérique et démarrez la capture pour commencer l&apos;auscultation
            </div>
          )}
        </main>
      </div>

      <StatusBar metrics={metrics} mode={mode} />

      <AudioPlayer
        isCapturing={isCapturing}
        onReady={handleAudioReady}
      />
    </div>
  );
}
