# SchoolRP Time Calculator

A lightweight, terminal-based utility designed for **Minecraft SchoolRP** players to accurately track **In-Character (IC) Time** and schedule events, synchronized with your **Real-World (OOC) Time**.

## Features

- **Accurate Time Conversion**: Automatically converts real seconds to in-game minutes (Default: 15s OOC = 1 min IC).
- **Day of Week Tracking**: Tracks Monday-Sunday cycles accurately.
- **Schedule Dashboard**: Displays upcoming classes, breaks, and events based on the official SchoolRP schedule.
- **Weekend Support**: Automatically detects weekends and adjusts the schedule display.
- **Configurable Speed**: Easily switch between **Standard** (15s/min), **Weekend** (10s/min), or **Custom** speeds to match server lag/events.
- **Prediction**: "What time will it be in-game at 5:00 PM IRL?" - calculate future IC times instantly.

## Installation

1.  **Install Python**: Ensure you have Python 3.6 or higher installed. [Download Python](https://www.python.org/downloads/)
2.  **Download Script**: Download `Schoolrptime.py` to a folder on your computer.

## Usage

1.  Open a terminal/command prompt in the folder.
2.  Run the script:
    ```bash
    python Schoolrptime.py
    ```
3.  **Sync**: On first run, select **Option 1 (SYNC)**.
    - Enter the current In-Game **Day** (e.g., `Monday`).
    - Enter the current In-Game **Time** (e.g., `12:00`).
4.  The dashboard will now live-update with the predicted IC time!

## Configuration

If the server speed seems off (e.g. during events or weekends), use **Option 4 (CONFIG)** to change the time scale.

- **Standard**: 15.0 seconds per IC minute.
- **Weekend**: 10.0 seconds per IC minute.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Kennedy
