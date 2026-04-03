import os
import sys
from datetime import datetime

import mss
import mss.tools


def take_screenshot(target_subfolder: str = "images") -> str:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(project_root, target_subfolder)

    os.makedirs(target_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.join(target_dir, f"screenshot_{timestamp}.png")

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=file_path)

    return file_path


if __name__ == "__main__":
    folder_name = "images"
    if len(sys.argv) > 1:
        folder_name = sys.argv[1]

    saved_path = take_screenshot(folder_name)
    print(saved_path)