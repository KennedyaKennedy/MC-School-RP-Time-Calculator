# SchoolRP Time Converter

An efficient, lightweight CLI tool for Minecraft SchoolRP players to track In-Character (IC) time and school schedules directly from their desktop.

## 🚀 Features
- **Persistent Calibration**: Synchronizes once and remembers. No need to log into the server to check the time.
- **Smart Estimation**: Uses your system clock to predict IC time based on the server's 15s/1m speed ratio $1:4$ (6 real hours = 24 IC hours).
- **Live Dashboard**: A clean command-line interface with real-time countdowns to major school events.
- **Predictive Mode**: Forecast what the in-game time will be at any point later today.

## 🛠️ Installation

1.  **Prerequisites**: Ensure you have [Python 3.7+](https://www.python.org/) installed.
2.  **Download**: Save `Schoolrptime.py` to your computer.
3.  **Run**:
    ```bash
    python Schoolrptime.py
    ```

## 📖 Usage Guide

*   **[SYNC]**: Enter the current IC time shown on the server boss bar. The tool automatically maps this to your local computer's time.
*   **[PREDICT]**: Enter a future real-life (OOC) time to see the corresponding IC time and class schedule for that moment.
*   **[REFRESH]**: Update the live countdowns immediately.

## 📝 License
Distributed under the **MIT License**. See the header in `Schoolrptime.py` for details.

---
(Note: The Calibration .json should not be deleted, that is what makes the script remember the time!)

*Created with ❤️ for the SchoolRP Community.*

