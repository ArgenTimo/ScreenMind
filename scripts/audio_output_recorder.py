import os
import signal
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from pynput import keyboard

from common.config import load_config
from common.logger import setup_logger


class OutputAudioRecorder:
    def __init__(self) -> None:
        self.config = load_config()
        self.project_dir = Path(self.config.project_dir)
        self.output_dir = self.project_dir / "audio_captures"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logs_dir = self.project_dir / self.config.default_log_dir
        self.logger = setup_logger(
            logs_dir=str(logs_dir),
            logger_name="screen_tool.audio_output_recorder",
            level=self.config.log_level,
        )

        self.process: subprocess.Popen | None = None
        self.lock = threading.Lock()
        self.is_recording = False
        self.current_file: Path | None = None
        self.hotkey = keyboard.Key.f8

    def _run_command(self, command: list[str]) -> str:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def _get_default_sink_name(self) -> str:
        sink_name = self._run_command(["pactl", "get-default-sink"]).strip()
        if not sink_name:
            raise RuntimeError("Could not determine default audio sink via pactl get-default-sink")
        return sink_name

    def _get_monitor_source_name(self) -> str:
        default_sink = self._get_default_sink_name()
        sources_output = self._run_command(["pactl", "list", "short", "sources"])

        candidates: list[str] = []
        for line in sources_output.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            source_name = parts[1]
            if source_name.endswith(".monitor"):
                candidates.append(source_name)

        exact_match = f"{default_sink}.monitor"
        if exact_match in candidates:
            return exact_match

        for candidate in candidates:
            if default_sink in candidate:
                return candidate

        if candidates:
            return candidates[0]

        raise RuntimeError("Could not find any PulseAudio/PipeWire monitor source")

    def _build_output_path(self) -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return self.output_dir / f"output_audio_{timestamp}.wav"

    def start_recording(self) -> None:
        with self.lock:
            if self.is_recording:
                return

            monitor_source = self._get_monitor_source_name()
            output_path = self._build_output_path()

            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "pulse",
                "-i",
                monitor_source,
                "-ac",
                "2",
                "-ar",
                "44100",
                str(output_path),
            ]

            self.logger.info("Starting output audio recording")
            self.logger.info("Using monitor source: %s", monitor_source)
            self.logger.info("Saving audio to: %s", output_path)

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            self.current_file = output_path
            self.is_recording = True

    def stop_recording(self) -> None:
        with self.lock:
            if not self.is_recording or self.process is None:
                return

            self.logger.info("Stopping output audio recording")

            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGINT)
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logger.warning("ffmpeg did not stop on SIGINT, killing")
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                self.process.wait(timeout=5)
            finally:
                self.logger.info("Saved output audio file: %s", self.current_file)
                self.process = None
                self.current_file = None
                self.is_recording = False

    def on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if key == self.hotkey:
            self.start_recording()

    def on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if key == self.hotkey:
            self.stop_recording()

    def run(self) -> None:
        self.logger.info("Audio output recorder listener started")
        self.logger.info("Hold F8 to record system output audio")

        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()


if __name__ == "__main__":
    recorder = OutputAudioRecorder()
    recorder.run()