"""
SchoolRP Time Converter
-----------------------
A lightweight utility for Minecraft SchoolRP players to track In-Character (IC) time 
and school schedules based on real-world (OOC) time.

License: MIT
Author: Kennedy
"""

import os
import json
from datetime import datetime
from typing import Optional, Tuple

# ==========================================
# CONFIGURATION
# ==========================================
# Time Speed: How many REAL SECONDS per ONE IC MINUTE.
# Based on "6 real hours per IC day": (6 * 60 * 60) / 1440 = 15 seconds.
REAL_SECONDS_PER_IC_MINUTE = 15.0 

CALIBRATION_FILE = "calibration.json"

# Official SchoolRP Weekday Schedule (IC Time)
SCHOOL_SCHEDULE = {
    "Gates Open": "07:30",
    "Breakfast": "08:00",
    "1st Period": "08:30",
    "Break / 2nd Period": "10:35",
    "Lunch": "12:00",
    "3rd Period": "12:45",
    "School Ends": "15:00"
}

IC_MIN_PER_DAY = 24 * 60

def time_to_min(time_str: str) -> Optional[int]:
    """Converts HH:MM string to total minutes from midnight."""
    try:
        if ":" not in time_str:
            return None
        h, m = map(int, time_str.split(':'))
        if not (0 <= h < 24 and 0 <= m < 60):
            return None
        return h * 60 + m
    except (ValueError, AttributeError):
        return None

def min_to_time(total_min: float) -> str:
    """Converts total minutes from midnight to HH:MM format."""
    total_min %= IC_MIN_PER_DAY
    h = int(total_min // 60)
    m = int(total_min % 60)
    return f"{h:02d}:{m:02d}"

class SchoolRPTimeBoard:
    """Manages the calibration and conversion logic for SchoolRP time."""
    
    def __init__(self):
        self.cal_ic_min: Optional[int] = None
        self.cal_real_dt: Optional[datetime] = None
        self.load_calibration()

    def load_calibration(self) -> bool:
        """Loads calibration data from a local JSON file."""
        if os.path.exists(CALIBRATION_FILE):
            try:
                with open(CALIBRATION_FILE, 'r') as f:
                    data = json.load(f)
                    self.cal_ic_min = data['ic_min']
                    self.cal_real_dt = datetime.fromisoformat(data['real_dt'])
                    return True
            except (json.JSONDecodeError, KeyError, ValueError):
                return False
        return False

    def save_calibration(self, ic_now_str: str) -> bool:
        """Saves current IC and local OOC time to a local JSON file."""
        ic_min = time_to_min(ic_now_str)
        if ic_min is None:
            return False
            
        self.cal_ic_min = ic_min
        self.cal_real_dt = datetime.now()
        
        data = {
            'ic_min': self.cal_ic_min,
            'real_dt': self.cal_real_dt.isoformat()
        }
        try:
            with open(CALIBRATION_FILE, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except IOError:
            return False

    def get_estimated_ic_now(self) -> Tuple[Optional[str], Optional[float]]:
        """Calculates current IC time based on system clock and calibration."""
        if self.cal_real_dt is None or self.cal_ic_min is None:
            return None, None
        
        delta_real = (datetime.now() - self.cal_real_dt).total_seconds()
        delta_ic_min = delta_real / REAL_SECONDS_PER_IC_MINUTE
        target_ic_min = (self.cal_ic_min + delta_ic_min) % IC_MIN_PER_DAY
        return min_to_time(target_ic_min), target_ic_min

    def get_ic_time_at(self, real_time_str: str) -> Tuple[Optional[str], Optional[float]]:
        """Calculates predicted IC time for a specific real-world HH:MM today."""
        if self.cal_real_dt is None or self.cal_ic_min is None:
            return None, None
            
        now = datetime.now()
        h_m = time_to_min(real_time_str)
        if h_m is None:
            return None, None
            
        h, m = h_m // 60, h_m % 60
        target_real_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            
        delta_real = (target_real_dt - self.cal_real_dt).total_seconds()
        delta_ic_min = delta_real / REAL_SECONDS_PER_IC_MINUTE
        target_ic_min = (self.cal_ic_min + delta_ic_min) % IC_MIN_PER_DAY
        return min_to_time(target_ic_min), target_ic_min

    def print_board(self, custom_ic_min: Optional[float] = None):
        """Displays the dashboard with current IC time and period countdowns."""
        ic_str, ic_min = self.get_estimated_ic_now()
        
        if custom_ic_min is not None:
            ic_min = custom_ic_min
            ic_str = min_to_time(ic_min)

        if ic_str is None or ic_min is None:
            print("\n[!] No calibration data available.")
            return

        print("\n" + "="*50)
        title = f" CURRENT IC TIME: {ic_str} "
        print(title.center(50, "="))
        print("="*50)
        
        if self.cal_real_dt:
            sync_time = self.cal_real_dt.strftime('%H:%M:%S')
            print(f" (Last Sync: {sync_time} OOC) ".center(50))
            print("-" * 50)
        
        print(f"{'PERIOD':<25} | {'IC TIME':<8} | {'REMAINING'}")
        print("-" * 50)
        
        for period, ic_time_str in SCHOOL_SCHEDULE.items():
            period_min = time_to_min(ic_time_str)
            if period_min is None: continue
            
            ic_wait = (period_min - ic_min) % IC_MIN_PER_DAY
            
            real_wait_total_sec = ic_wait * REAL_SECONDS_PER_IC_MINUTE
            h = int(real_wait_total_sec // 3600)
            m = int((real_wait_total_sec % 3600) // 60)
            s = int(real_wait_total_sec % 60)
            
            countdown = "NOW" if ic_wait < 1 else f"{h}h {m}m {s}s"
            print(f"{period:<25} | {ic_time_str:<8} | {countdown}")
        print("="*50)

def main():
    board = SchoolRPTimeBoard()
    
    while True:
        # Clear screen for a better dashboard feel
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n--- SchoolRP OOC Time Dashboard ---")
        
        if board.cal_real_dt:
            board.print_board()
        else:
            print("\n[!] Dashboard Offline: No Calibration Data.")
            print("Please perform an IC Sync (Option 1) to start.")
        
        print("\n[Menu Options]")
        print("1. [SYNC]    Update with current in-game time")
        print("2. [PREDICT] What time will it be at ...?")
        print("3. [REFRESH] Update countdowns")
        print("q. [QUIT]    Close the dashboard")
        
        choice = input("\nSelect: ").strip().lower()
        
        if choice == '1':
            ic = input("\nWhat is the EXACT IC Time right now? (HH:MM): ").strip()
            if board.save_calibration(ic):
                input(f"\n[✓] Sync Successful! Locked IC {ic} to your local time {board.cal_real_dt.strftime('%H:%M:%S')}.\nPress Enter to return.")
            else:
                input("\n[!] Error: Invalid format. Please use HH:MM (e.g. 08:30).\nPress Enter to try again.")
                
        elif choice == '2':
            ooc = input("\nEnter Target Real (OOC) Time (HH:MM): ").strip()
            ic_str, ic_min = board.get_ic_time_at(ooc)
            if ic_str:
                print(f"\n>>> At {ooc} OOC, the server will be at approximately {ic_str} IC.")
                board.print_board(custom_ic_min=ic_min)
                input("\nPress Enter to return to live dashboard.")
            else:
                input("\n[!] Error: Invalid format. Use HH:MM.\nPress Enter to return.")
                
        elif choice == '3':
            continue 
                
        elif choice == 'q':
            print("\nExiting")
            break

if __name__ == "__main__":
    main()
