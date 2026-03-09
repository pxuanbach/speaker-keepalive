import time
from typing import List, Optional

import numpy as np
import pyaudio

# Default device name from the original script
DEVICE_NAME = "ACTON III"


def list_output_devices() -> List[dict]:
    """Return a list of available output devices as dicts with `index` and `name`."""
    pa = pyaudio.PyAudio()
    devices = []
    try:
        info = pa.get_host_api_info_by_index(0)
        count = int(info.get("deviceCount", 0))
        for i in range(count):
            device = pa.get_device_info_by_index(i)
            # Only include devices that support output
            if device.get("maxOutputChannels", 0) > 0:
                devices.append({"index": i, "name": device.get("name")})
    finally:
        pa.terminate()
    return devices


def get_output_device_index(device_name: str) -> Optional[int]:
    """Find a matching output device by exact name, return its index or None."""
    pa = pyaudio.PyAudio()
    try:
        info = pa.get_host_api_info_by_index(0)
        count = int(info.get("deviceCount", 0))
        for i in range(count):
            device = pa.get_device_info_by_index(i)
            if device.get("name") == device_name and device.get("maxOutputChannels", 0) > 0:
                return i
    finally:
        pa.terminate()
    return None


def play_tone(device_name: str = DEVICE_NAME,
              duration: float = 0.5,
              frequency: float = 5000000.0,
              amplitude: float = 0.5,
              rate: int = 44100) -> bool:
    """Play a sine tone to the named output device.

    Returns True if tone was sent, False if device not found or an error occurred.
    """
    # Validate frequency against Nyquist
    if frequency >= rate / 2:
        print(f"Requested frequency {frequency}Hz exceeds Nyquist (rate/2). Reducing to {rate/2 - 1}Hz")
        frequency = rate / 2 - 1

    pa = pyaudio.PyAudio()
    output_index = get_output_device_index(device_name)
    if output_index is None:
        print(f"{device_name} not found in output devices, skipping")
        return False

    print(f"Sending tone to {device_name} (device index {output_index}) freq={frequency}Hz dur={duration}s")
    try:
        stream = pa.open(format=pyaudio.paInt16,
                         channels=1,
                         rate=rate,
                         output=True,
                         output_device_index=output_index)

        frame_count = int(rate * duration)
        samples = np.sin(2 * np.pi * frequency * np.arange(frame_count) / rate)
        # scale to int16
        max_int16 = np.iinfo(np.int16).max
        tone = (samples * amplitude * max_int16).astype(np.int16)
        stream.write(tone.tobytes())
        # Ensure playback finishes
        time.sleep(duration)
        stream.stop_stream()
        stream.close()
    except Exception as exc:  # pragma: no cover - hardware-dependent
        print(f"Error playing tone: {exc}")
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        pa.terminate()
        return False

    pa.terminate()
    return True


if __name__ == "__main__":
    # Backwards-compat quick test
    print("Available output devices:")
    for d in list_output_devices():
        print(f"{d['index']}: {d['name']}")
