import os
import signal
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from pynput import keyboard

from analyze_screenshot import send_session_to_telegram
from common.config import load_config
from common.logger import setup_logger
from send_telegram import send_message
from take_screenshot import take_screenshot


def _cleanup_capture_folder(folder: Path, logger) -> int:
    removed = 0
    if not folder.is_dir():
        return 0
    for entry in folder.iterdir():
        if entry.is_file() and entry.name != ".gitkeep":
            logger.info("Startup cleanup removing: %s", entry)
            entry.unlink()
            removed += 1
    return removed


class OutputAudioRecorder:
    def __init__(self) -> None:
        self.config = load_config()
        self.project_dir = Path(self.config.project_dir)
        self.output_dir = self.project_dir / "audio_captures"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.project_dir / self.config.default_image_dir
        self.images_dir.mkdir(parents=True, exist_ok=True)

        logs_dir = self.project_dir / self.config.default_log_dir
        self.logger = setup_logger(
            logs_dir=str(logs_dir),
            logger_name="screen_tool.audio_output_recorder",
            level=self.config.log_level,
        )
        self.logger.info(
            "Service config: DEBUG_TELEGRAM=%s DEFAULT_IMAGE_DIR=%s",
            self.config.debug_telegram,
            self.config.default_image_dir,
        )
        self.logger.info("Unified activity log: %s", logs_dir / "service.log")

        self.process: subprocess.Popen | None = None
        self.lock = threading.Lock()
        self.is_recording = False
        self.current_file: Path | None = None
        self.record_hotkey = keyboard.Key.f8
        self.screenshot_hotkey = keyboard.Key.f9
        self.batch_hotkey = keyboard.Key.f2
        self._last_f9_screenshot = 0.0
        self._f9_debounce_seconds = 0.5
        self._batch_lock = threading.Lock()
        self._batch_running = False

        n_img = _cleanup_capture_folder(self.images_dir, self.logger)
        n_aud = _cleanup_capture_folder(self.output_dir, self.logger)
        self.logger.info(
            "Startup cleanup finished: removed %s image file(s), %s audio file(s) under %s and %s (.gitkeep kept)",
            n_img,
            n_aud,
            self.images_dir,
            self.output_dir,
        )

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

    def _take_screenshot_safe(self) -> None:
        now = time.time()
        if now - self._last_f9_screenshot < self._f9_debounce_seconds:
            self.logger.debug("F9 ignored (debounce %.2fs)", self._f9_debounce_seconds)
            return
        self._last_f9_screenshot = now
        try:
            path = take_screenshot(self.config.default_image_dir)
            self.logger.info("Screenshot saved (F9): %s", path)
        except Exception:
            self.logger.exception("Screenshot capture failed")

    def _request_batch_analyze(self) -> None:
        with self._batch_lock:
            if self._batch_running:
                self.logger.info("Session analysis already running; ignoring F2")
                return
            self._batch_running = True
        threading.Thread(target=self._batch_analyze_worker, daemon=True).start()

    def _batch_analyze_worker(self) -> None:
        try:
            pngs = sorted(self.images_dir.glob("*.png"))
            wavs = sorted(self.output_dir.glob("*.wav"))
            paths_png = [str(p) for p in pngs]
            paths_wav = [str(p) for p in wavs]

            self.logger.info(
                "F2 batch: %s screenshot(s), %s audio file(s)",
                len(paths_png),
                len(paths_wav),
            )

            if not paths_png and not paths_wav:
                self.logger.info("F2 batch: empty session, sending hint to Telegram")
                send_message("Session analysis: no screenshots or audio to send. Use F9 and F8 first.")
                return
            if not paths_png:
                self.logger.info("F2 batch: no PNGs, sending hint to Telegram")
                send_message("Session analysis: add at least one screenshot (F9) before running the pipeline.")
                return

            prompt_path = str(self.project_dir / self.config.default_prompt_path)
            self.logger.info("F2 batch: running pipeline and Telegram (delete after send if not DEBUG_TELEGRAM)")
            send_session_to_telegram(paths_png, paths_wav, prompt_path)
            self.logger.info("F2 batch: send_session_to_telegram finished")
        except Exception:
            self.logger.exception("Session analysis failed")
            try:
                send_message("Session analysis failed; check logs.")
            except Exception:
                self.logger.exception("Could not send Telegram error")
        finally:
            with self._batch_lock:
                self._batch_running = False

    def on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if key == self.record_hotkey:
            self.logger.debug("Hotkey press: F8 (record)")
            self.start_recording()
        elif key == self.screenshot_hotkey:
            self.logger.debug("Hotkey press: F9 (screenshot)")
            self._take_screenshot_safe()
        elif key == self.batch_hotkey:
            self.logger.info("Hotkey press: F2 (session → pipeline)")
            self._request_batch_analyze()

    def on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if key == self.record_hotkey:
            self.logger.debug("Hotkey release: F8 (stop record)")
            self.stop_recording()

    def run(self) -> None:
        self.logger.info("Screen tool hotkey listener started")
        self.logger.info(
            "F8 hold=record audio, F9=screenshot, F2=send session (screenshots+audio) to pipeline/Telegram"
        )

        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()


if __name__ == "__main__":
    recorder = OutputAudioRecorder()
    recorder.run()