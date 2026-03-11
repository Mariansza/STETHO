"""WebSocket endpoint handler for audio streaming."""

import asyncio
import logging
import time

from fastapi import WebSocket, WebSocketDisconnect

from backend.audio.capture import AudioCapture
from backend.audio.playback import AudioPlayback
from backend.dsp.pipeline import DSPPipeline
from backend.analysis.spectral import SpectralAnalyzer
from backend.websocket.protocol import (
    encode_audio_frame,
    encode_viz_message,
    decode_client_message,
)
from backend.config import VIZ_INTERVAL

logger = logging.getLogger(__name__)


class AudioWebSocketHandler:
    """Manages a single WebSocket session: capture → DSP → stream."""

    def __init__(self) -> None:
        self.capture = AudioCapture()
        self.playback = AudioPlayback()
        self.pipeline = DSPPipeline(mode="cardiac")
        self.analyzer = SpectralAnalyzer()
        self._seq: int = 0
        self._running: bool = False

    async def handle(self, ws: WebSocket) -> None:
        """Main WebSocket lifecycle."""
        await ws.accept()
        logger.info("WebSocket client connected")

        receive_task = asyncio.create_task(self._receive_loop(ws))

        try:
            await self._stream_loop(ws)
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error("WebSocket error: %s", e)
        finally:
            receive_task.cancel()
            if self.capture.running:
                await self.capture.stop()
            if self.playback.running:
                self.playback.stop()
            self._running = False

    async def _stream_loop(self, ws: WebSocket) -> None:
        """Read from capture queue, process, and send to client."""
        last_viz_time = 0.0

        while True:
            if not self.capture.running:
                await asyncio.sleep(0.05)
                continue

            try:
                chunk = await asyncio.wait_for(
                    self.capture.read_chunk(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            # DSP processing
            processed = self.pipeline.process(chunk)

            # Play audio directly through system speakers (no browser audio)
            self.playback.feed(processed)

            # Send binary audio frame to frontend (for waveform visualization)
            self._seq += 1
            frame = encode_audio_frame(self._seq, processed)
            await ws.send_bytes(frame)

            # Send viz data at lower rate
            now = time.monotonic()
            if now - last_viz_time >= VIZ_INTERVAL:
                viz_data = self.analyzer.analyze(processed)
                await ws.send_text(encode_viz_message(viz_data))
                last_viz_time = now

    async def _receive_loop(self, ws: WebSocket) -> None:
        """Listen for control messages from the client."""
        try:
            while True:
                raw = await ws.receive_text()
                msg = decode_client_message(raw)
                await self._handle_message(msg, ws)
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass

    async def _handle_message(self, msg: dict, ws: WebSocket) -> None:
        """Route a client control message."""
        msg_type = msg.get("type")

        if msg_type == "start_capture":
            device_id = msg.get("device_id")
            await self.capture.start(device_id=device_id)
            # Sync pipeline sample rate with actual device sample rate
            sr = self.capture.sample_rate
            self.pipeline.set_sample_rate(sr)
            self.analyzer = SpectralAnalyzer()
            # Start direct audio playback to system speakers
            self.playback.start(sr)
            self._running = True
            # Tell the frontend the actual sample rate
            await ws.send_text(encode_viz_message({
                "type": "config",
                "sample_rate": sr,
            }))
            logger.info("Capture started (device=%s, sr=%d)", device_id, sr)

        elif msg_type == "stop_capture":
            await self.capture.stop()
            self.playback.stop()
            self._running = False
            logger.info("Capture stopped")

        elif msg_type == "set_mode":
            mode = msg.get("mode", "cardiac")
            self.pipeline.set_mode(mode)
            logger.info("Mode changed to: %s", mode)

        elif msg_type == "set_passthrough":
            enabled = msg.get("enabled", False)
            self.pipeline.set_passthrough(enabled)
            logger.info("Passthrough: %s", enabled)

        elif msg_type == "set_params":
            params = msg.get("params", {})
            self.pipeline.set_bandpass_params(
                low_cut=params.get("low_cut"),
                high_cut=params.get("high_cut"),
                filter_order=params.get("filter_order"),
            )
            if "gain" in params:
                self.pipeline.set_gain(params["gain"])
            logger.info("Params updated: %s", params)

        elif msg_type == "set_device":
            device_id = msg.get("device_id")
            was_running = self.capture.running
            if was_running:
                await self.capture.stop()
            if was_running:
                await self.capture.start(device_id=device_id)
                self.pipeline.set_sample_rate(self.capture.sample_rate)
            logger.info("Device changed to: %s (sr=%d)",
                        device_id, self.capture.sample_rate)

        elif msg_type == "set_noise_reduction":
            self.pipeline.noise_reducer.set_params(
                alpha=msg.get("alpha"),
                beta=msg.get("beta"),
            )
            logger.info("Noise reduction updated: alpha=%s beta=%s",
                        msg.get("alpha"), msg.get("beta"))

        elif msg_type == "recalibrate_noise":
            if self.capture.running:
                self.pipeline.noise_reducer.start_calibration()
                for _ in range(20):
                    try:
                        cal_chunk = await asyncio.wait_for(
                            self.capture.read_chunk(), timeout=1.0
                        )
                        self.pipeline.noise_reducer.add_calibration_frame(cal_chunk)
                    except asyncio.TimeoutError:
                        break
                self.pipeline.noise_reducer.finish_calibration()
                logger.info("Noise calibration completed")

        else:
            logger.warning("Unknown message type: %s", msg_type)
