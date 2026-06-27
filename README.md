# Kobel-vibecode-helper

Automatically clicks "Accept All" for Vibe Coders coding on Windsurf.

## Features

- Automatically accepts code changes in Windsurf
- GUI with dark theme
- Image recognition to find and click Accept All button
- Hotkey support (F7) for easy start/stop
- Fail-safe protection (move mouse to screen corner to abort)
- Tracks number of accepts performed
- Mouse position restoration - returns cursor to original position after clicking

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

1. Take a screenshot of the "Accept All" button in Windsurf
2. Save it as `accept_all_button.png` in the same directory as this script
3. Make sure Windsurf is visible on your screen

## Usage

1. Run the program:
   ```bash
   python vibe_code_helper.py
   ```

2. Press **F7** or click the button to start/stop the automation
3. Adjust the check interval as needed
4. Close the window to quit

## How It Works

The program uses image recognition to find the "Accept All" button on your screen and click it automatically. It checks at the configured interval for the button. After clicking, it restores the mouse cursor to its original position to minimize disruption.

## Safety Features

- **Fail-safe**: Move your mouse to any corner of the screen to immediately stop the automation
- **Hotkey control**: Use F7 from anywhere to start/stop

## Requirements

- Python 3.8+
- pyautogui
- keyboard
- Pillow

## Notes

- This tool is designed for Windsurf and requires a screenshot of the Accept All button to work
- The image recognition approach is more reliable than keyboard shortcuts for this use case
- The mouse position restoration feature helps minimize disruption when typing or working

## License

Use at your own risk. This tool is provided as-is for educational purposes.
