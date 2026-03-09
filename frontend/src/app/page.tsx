"use client";

import { useCallback, useRef, useState } from "react";
import type { AudioMetrics, ListeningMode, VizMessage } from "@/types";
import { useWebSocket } from "@/hooks/use-websocket";
import { MODE_COLORS } from "@/lib/constants";
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
    <div className="h-screen flex flex-col bg-[var(--bg-primary)]">
      <Header connectionStatus={status} isCapturing={isCapturing} />

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <aside className="w-[280px] border-r border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 space-y-5 overflow-y-auto flex-shrink-0">
          <DeviceSelector
            onSelect={handleDeviceSelect}
            selectedDeviceId={deviceId}
          />
          <div className="h-px bg-[var(--border-subtle)]" />
          <ControlPanel
            mode={mode}
            isCapturing={isCapturing}
            onSend={handleSend}
            onStartCapture={handleStartCapture}
            onStopCapture={handleStopCapture}
          />
        </aside>

        {/* Main content */}
        <main className="flex-1 p-6 space-y-5 overflow-y-auto bg-[var(--bg-primary)]">
          <WaveformCanvas
            samples={waveformSamples}
            color={MODE_COLORS[mode]}
            height={180}
          />
          <SpectrogramCanvas row={spectrogramRow} height={240} />

          {/* Empty state */}
          {!isCapturing && !waveformSamples && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-16 h-16 rounded-2xl bg-[var(--bg-elevated)] border border-[var(--border-subtle)] flex items-center justify-center mb-4">
                <svg viewBox="0 0 24 24" className="w-7 h-7 text-[var(--text-muted)]" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path d="M12 3c-1.5 0-4 1-4 4v2c0 1.5.5 2 2 2h4c1.5 0 2-.5 2-2V7c0-3-2.5-4-4-4z" />
                  <path d="M8 9l-2 1.5c-1 .8-1.5 2-1.5 3.2 0 2 1.5 3.3 3.5 3.3" />
                  <path d="M16 9l2 1.5c1 .8 1.5 2 1.5 3.2 0 2-1.5 3.3-3.5 3.3" />
                  <path d="M10 17v3.5a1.5 1.5 0 003 0V17" />
                </svg>
              </div>
              <p className="text-sm text-[var(--text-secondary)] mb-1">
                Pr&ecirc;t pour l&apos;auscultation
              </p>
              <p className="text-xs text-[var(--text-muted)] max-w-[280px]">
                S&eacute;lectionnez un p&eacute;riph&eacute;rique audio USB et d&eacute;marrez la capture pour commencer
              </p>
            </div>
          )}
        </main>
      </div>

      <StatusBar metrics={metrics} mode={mode} />

      <AudioPlayer isCapturing={isCapturing} onReady={handleAudioReady} />
    </div>
  );
}
