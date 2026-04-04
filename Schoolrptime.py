import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Set

# Audio Alert Setup
try:
    import winsound

    def play_beep():
        winsound.Beep(1000, 500)
except ImportError:

    def play_beep():
        print("\a", end="", flush=True)


# Constants - Hardcoded so they can't break
SPEED_STANDARD = 15.0  # Mon-Fri
SPEED_WEEKEND = 10.0  # Sat-Sun
ALERT_LEAD_IC = 5  # Beep 5 IC mins before class
CALIBRATION_FILE = "calibration.json"
DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
IC_MIN_PER_DAY = 1440
ALERT_EPSILON = 0.5  # Tolerance for float comparison in alerts

SCHOOL_SCHEDULE: Dict[str, str] = {
    "Start of Day": "07:30",
    "Breakfast": "08:00",
    "Period 1": "08:30",
    "Period 2": "08:55",
    "Break": "10:35",
    "Period 3": "10:55",
    "Lunch": "12:35",
    "Period 4": "13:20",
    "End of Day": "15:00",
}


def match_day(input_str: str) -> Optional[int]:
    """Match user input to a day index, handling abbreviations unambiguously."""
    if not input_str:
        return None
    # Exact match first
    for i, d in enumerate(DAYS_OF_WEEK):
        if d.lower() == input_str.lower():
            return i
    # Case-insensitive prefix match — require at least 3 chars to disambiguate Sat/Sun
    if len(input_str) < 3:
        return None
    for i, d in enumerate(DAYS_OF_WEEK):
        if d.lower().startswith(input_str.lower()):
            return i
    return None


class SchoolRPTimeBoard:
    def __init__(self):
        self.cal_ic_total_min: Optional[float] = None
        self.cal_real_dt: Optional[datetime] = None
        self.played_alerts: Set[str] = set()
        self.last_alert_day: Optional[str] = None
        self.current_speed: float = SPEED_STANDARD
        self.load_calibration()

    def load_calibration(self):
        if os.path.exists(CALIBRATION_FILE):
            try:
                with open(CALIBRATION_FILE, "r") as f:
                    data = json.load(f)
                    self.cal_ic_total_min = data.get("ic_total_min")
                    if data.get("real_dt"):
                        self.cal_real_dt = datetime.fromisoformat(data["real_dt"])
            except (json.JSONDecodeError, ValueError, OSError, KeyError):
                pass

    def save_calibration(self, ic_time_str: str, ic_day_idx: int) -> bool:
        try:
            h, m = map(int, ic_time_str.split(":"))
            if not (0 <= h <= 23 and 0 <= m <= 59):
                return False
            day_min = h * 60 + m
            self.cal_ic_total_min = (ic_day_idx * IC_MIN_PER_DAY) + day_min
            self.cal_real_dt = datetime.now()
            with open(CALIBRATION_FILE, "w") as f:
                json.dump(
                    {
                        "ic_total_min": self.cal_ic_total_min,
                        "real_dt": self.cal_real_dt.isoformat(),
                    },
                    f,
                )
            self.played_alerts.clear()
            self.last_alert_day = None
            return True
        except (ValueError, OSError):
            return False

    def get_status(
        self, target_dt: Optional[datetime] = None
    ) -> Optional[Tuple[str, str, float, float]]:
        if not self.cal_real_dt or self.cal_ic_total_min is None:
            return None

        now_dt = target_dt or datetime.now()
        delta_sec = (now_dt - self.cal_real_dt).total_seconds()

        # If target is in the past, project forward by whole days until future
        if delta_sec < 0:
            days_ahead = int(abs(delta_sec) / 86400) + 1
            now_dt = now_dt + timedelta(days=days_ahead)
            delta_sec = (now_dt - self.cal_real_dt).total_seconds()

        # Iteratively resolve speed/day until stable (max 2 flips: weekday<->weekend)
        active_speed = self.current_speed
        total_ic_min = self.cal_ic_total_min + (delta_sec / active_speed)
        day_idx = int(total_ic_min // IC_MIN_PER_DAY) % 7
        for _ in range(2):
            new_speed = SPEED_WEEKEND if day_idx >= 5 else SPEED_STANDARD
            if new_speed == active_speed:
                break
            active_speed = new_speed
            total_ic_min = self.cal_ic_total_min + (delta_sec / active_speed)
            day_idx = int(total_ic_min // IC_MIN_PER_DAY) % 7

        day_name = DAYS_OF_WEEK[day_idx]
        min_in_day = total_ic_min % IC_MIN_PER_DAY

        h, m = int(min_in_day // 60), int(min_in_day % 60)
        return day_name, f"{h:02d}:{m:02d}", min_in_day, active_speed

    def check_alerts(self, day: str, ic_min: float):
        if day in ("Saturday", "Sunday"):
            return
        # Reset alerts when the IC day changes
        if self.last_alert_day != day:
            self.played_alerts.clear()
            self.last_alert_day = day
        for period, p_time in SCHOOL_SCHEDULE.items():
            p_m = int(p_time.split(":")[0]) * 60 + int(p_time.split(":")[1])
            diff = p_m - ic_min
            if (
                diff > ALERT_EPSILON
                and diff <= ALERT_LEAD_IC + ALERT_EPSILON
                and period not in self.played_alerts
            ):
                play_beep()
                self.played_alerts.add(period)

    def print_dashboard(self):
        os.system("cls" if os.name == "nt" else "clear")
        result = self.get_status()
        if result is None:
            print("\n[!] SYSTEM OFFLINE: Please Sync (Option 1) to anchor the time.")
            return
        day, time_str, ic_min, speed = result

        self.check_alerts(day, ic_min)
        print(f"\n{'=' * 40}\n {day} {time_str} | Speed: {int(speed)}s\n{'=' * 40}")

        if day in ("Saturday", "Sunday"):
            print(f"{'WEEKEND - NO SCHOOL':^40}")
        else:
            for p, pt in sorted(SCHOOL_SCHEDULE.items(), key=lambda x: x[1]):
                p_m = int(pt.split(":")[0]) * 60 + int(pt.split(":")[1])
                diff = p_m - ic_min
                status = (
                    "PASSED"
                    if diff < 0
                    else "NOW"
                    if diff < 1
                    else f"{int(diff * speed)}s"
                )
                print(f"{p:<15} | {pt} | {status}")
        print("=" * 40)

    def configure_speed(self):
        """Allow user to change the active speed."""
        print("\n--- Speed Configuration ---")
        print(f"1: Standard ({int(SPEED_STANDARD)}s per IC min)")
        print(f"2: Weekend ({int(SPEED_WEEKEND)}s per IC min)")
        print("3: Custom")
        print("4: Cancel")
        choice = input(">> ").strip()
        if choice == "1":
            self.current_speed = SPEED_STANDARD
            print(f"Speed set to Standard ({int(self.current_speed)}s/min).")
        elif choice == "2":
            self.current_speed = SPEED_WEEKEND
            print(f"Speed set to Weekend ({int(self.current_speed)}s/min).")
        elif choice == "3":
            try:
                val = float(input("Enter seconds per IC minute: "))
                if val > 0:
                    self.current_speed = val
                    print(f"Custom speed set to {val}s/min.")
                else:
                    print("Speed must be positive.")
            except ValueError:
                print("Invalid number.")
        else:
            print("Cancelled.")
        time.sleep(1)


def main():
    board = SchoolRPTimeBoard()
    while True:
        board.print_dashboard()
        print("\n1: SYNC | 2: PREDICT | 3: REFRESH | 4: CONFIG | Q: QUIT")
        choice = input(">> ").lower().strip()
        if choice == "1":
            d_str = input("Day (Mon/Sat/etc): ").strip()
            d_idx = match_day(d_str)
            t_str = input("Time (HH:MM): ").strip()
            if d_idx is not None and board.save_calibration(t_str, d_idx):
                print("Synced!")
            else:
                print("Invalid Input.")
            time.sleep(1)
        elif choice == "2":
            t_ooc = input("Real Time (HH:MM): ").strip()
            try:
                h, m = map(int, t_ooc.split(":"))
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    print("Invalid time.")
                    time.sleep(1)
                    continue
                target = datetime.now().replace(
                    hour=h, minute=m, second=0, microsecond=0
                )
                res = board.get_status(target)
                if res is not None:
                    print(f"\nPrediction: {res[0]} {res[1]}")
                else:
                    print("\n[!] No calibration data. Sync first.")
                input("Press Enter...")
            except (ValueError, OSError):
                print("Invalid format.")
                time.sleep(1)
        elif choice == "3":
            # REFRESH: immediately re-render dashboard
            continue
        elif choice == "4":
            board.configure_speed()
        elif choice == "q":
            break
        else:
            time.sleep(0.5)


if __name__ == "__main__":
    main()
