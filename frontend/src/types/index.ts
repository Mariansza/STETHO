export type ListeningMode = "cardiac" | "respiratory" | "raw";

export interface AudioMetrics {
  rms_db: number;
  peak_db: number;
  snr: number;
  dominant_freq: number;
}

export interface WaveformData {
  min: number;
  max: number;
}

export interface VizMessage {
  type: "viz";
  waveform: WaveformData;
  spectrogram_row: number[];
  metrics: AudioMetrics;
}

export interface AudioDevice {
  id: number;
  name: string;
  channels: number;
  sample_rate: number;
  hostapi: string;
}

export interface DSPParams {
  low_cut?: number;
  high_cut?: number;
  gain?: number;
  filter_order?: number;
}

export type ClientMessage =
  | { type: "start_capture"; device_id?: number }
  | { type: "stop_capture" }
  | { type: "set_mode"; mode: ListeningMode }
  | { type: "set_params"; params: DSPParams }
  | { type: "set_device"; device_id: number }
  | { type: "set_noise_reduction"; alpha: number; beta: number }
  | { type: "recalibrate_noise" };

export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";
