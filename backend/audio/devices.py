"""Audio device discovery and selection."""

import sounddevice as sd


def list_devices() -> list[dict]:
    """List all available input audio devices."""
    devices = sd.query_devices()
    result: list[dict] = []
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            result.append({
                "id": i,
                "name": dev["name"],
                "channels": dev["max_input_channels"],
                "sample_rate": dev["default_samplerate"],
                "hostapi": sd.query_hostapis(dev["hostapi"])["name"],
            })
    return result


def get_device_info(device_id: int) -> dict | None:
    """Get info for a specific device."""
    try:
        dev = sd.query_devices(device_id)
        if dev["max_input_channels"] > 0:
            return {
                "id": device_id,
                "name": dev["name"],
                "channels": dev["max_input_channels"],
                "sample_rate": dev["default_samplerate"],
                "hostapi": sd.query_hostapis(dev["hostapi"])["name"],
            }
    except Exception:
        pass
    return None
