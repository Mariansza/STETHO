"use client";

import { useCallback, useState } from "react";
import type { AudioMetrics, ConfigMessage, ListeningMode, VizMessage } from "@/types";
import { useWebSocket } from "@/hooks/use-websocket";
import { MODE_COLORS } from "@/lib/constants";
import { Header } from "@/components/header";
import { DeviceSelector } from "@/components/device-selector";
import { ControlPanel } from "@/components/control-panel";
import { WaveformCanvas } from "@/components/waveform-canvas";
import { SpectrogramCanvas } from "@/components/spectrogram-canvas";
// Audio playback is now handled directly by the backend (sounddevice output)
// import { AudioPlayer } from "@/components/audio-player";
import { StatusBar } from "@/components/status-bar";

export default function Home() {
  const [mode, setMode] = useState<ListeningMode>("cardiac");
  const [isCapturing, setIsCapturing] = useState(false);
  const [deviceId, setDeviceId] = useState<number | null>(null);
  const [metrics, setMetrics] = useState<AudioMetrics | null>(null);
  const [waveformSamples, setWaveformSamples] = useState<Float32Array | null>(null);
  const [spectrogramRow, setSpectrogramRow] = useState<number[] | null>(null);
  const [sampleRate, setSampleRate] = useState(44100);

  const onAudioFrame = useCallback((pcm: Float32Array) => {
    setWaveformSamples(pcm);
  }, []);

  const onVizMessage = useCallback((viz: VizMessage) => {
    setMetrics(viz.metrics);
    setSpectrogramRow(viz.spectrogram_row);
  }, []);

  const onConfig = useCallback((config: ConfigMessage) => {
    setSampleRate(config.sample_rate);
  }, []);

  const { status, connect, send } = useWebSocket({
    onAudioFrame,
    onVizMessage,
    onConfig,
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
            height={200}
          />
          <SpectrogramCanvas row={spectrogramRow} height={220} />

          {/* Empty state */}
          {!isCapturing && !waveformSamples && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-16 h-16 rounded-2xl bg-[var(--bg-elevated)] border border-[var(--border-subtle)] flex items-center justify-center mb-4">
                <svg viewBox="0 0 32 32" className="w-8 h-8" fill="none">
                  <rect x="2" y="12" width="2.5" height="8" rx="1.25" fill="var(--text-muted)" opacity="0.5" />
                  <rect x="7" y="8" width="2.5" height="16" rx="1.25" fill="var(--text-muted)" opacity="0.6" />
                  <rect x="12" y="4" width="2.5" height="24" rx="1.25" fill="var(--text-muted)" opacity="0.7" />
                  <rect x="17" y="6" width="2.5" height="20" rx="1.25" fill="var(--text-muted)" opacity="0.65" />
                  <rect x="22" y="10" width="2.5" height="12" rx="1.25" fill="var(--text-muted)" opacity="0.55" />
                  <rect x="27" y="13" width="2.5" height="6" rx="1.25" fill="var(--text-muted)" opacity="0.4" />
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

      {/* Audio playback handled by backend (sounddevice direct output) */}
    </div>
  );
}
