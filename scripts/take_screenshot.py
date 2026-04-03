import os
import sys
from datetime import datetime

import mss
import mss.tools

from common.config import load_config
from common.logger import setup_logger


def take_screenshot(target_subfolder: str) -> str:
    config = load_config()
    logs_dir = os.path.join(config.project_dir, config.default_log_dir)
    logger = setup_logger(logs_dir=logs_dir, logger_name="screen_tool.screenshot", level=config.log_level)

    logger.info("Starting screenshot capture")
    logger.info("Requested target subfolder: %s", target_subfolder)

    target_dir = os.path.join(config.project_dir, target_subfolder)
    os.makedirs(target_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.join(target_dir, f"screenshot_{timestamp}.png")

    logger.info("Resolved screenshot path: %s", file_path)

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        logger.info("Using primary monitor index 1 with geometry: %s", monitor)
        screenshot = sct.grab(monitor)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=file_path)

    logger.info("Screenshot saved successfully: %s", file_path)
    return file_path


if __name__ == "__main__":
    config = load_config()
    folder_name = config.default_image_dir

    if len(sys.argv) > 1:
        folder_name = sys.argv[1]

    saved_path = take_screenshot(folder_name)
    print(saved_path)