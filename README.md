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
- **Millisecond precision** for click intervals (competitive feature)
- **Save/Load settings** - save your preferred configurations to JSON files
- **Click statistics** - real-time session statistics including clicks per minute
- **Global leaderboard** - compete with other users worldwide
- **Automatic leaderboard submission** - submit your sessions via GitHub API or manual GitHub Issues

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

2. On first launch, you'll be asked if you want to participate in the global leaderboard
3. If yes, enter a unique username and optionally provide a GitHub token for automatic submission
4. Press **F7** or click the button to start/stop the automation
5. Adjust the check interval (in milliseconds) as needed
6. Use "Save Settings" to save your configuration to a JSON file
7. Use "Load Settings" to load a previously saved configuration
8. Monitor real-time statistics including clicks per minute
9. Click "View Leaderboard" to see the global rankings
10. When you stop a session, you'll be prompted to submit your results to the leaderboard
11. Close the window to quit

## Leaderboard

The global leaderboard tracks accepts per minute from all users worldwide. 

**Automatic Submission (Recommended):**
- Provide a GitHub token during setup for automatic submission
- Your sessions are submitted directly to the leaderboard via GitHub API
- Requires a GitHub token with 'repo' scope (you create this yourself)

**Manual Submission:**
- If you don't provide a token, you can submit via GitHub Issues
- The app will open a pre-filled GitHub Issue with your session data
- Your data will be added to the leaderboard manually

**Viewing the Leaderboard:**
- Click "View Leaderboard" in the app to see the top 20 users
- Leaderboard is sorted by accepts per minute (descending)
- Data is fetched from GitHub in real-time

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
