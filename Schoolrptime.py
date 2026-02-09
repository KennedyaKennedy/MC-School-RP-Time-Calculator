"""
SchoolRP Time Calculator
------------------------
A comprehensive utility for Minecraft SchoolRP players to track In-Character (IC) time, 
days of the week, and school schedules, synchronized with real-world (OOC) time.

Features:
- Accurate conversion (Default: 15s OOC = 1 min IC).
- Day of Week tracking (Monday-Sunday).
- Official SchoolRP Schedule display.
- Configurable time speed for events/weekends.

Author: Kennedy
License: MIT

Copyright (c) 2026 Kennedy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import json
import sys
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Union

# ==========================================
# CONFIGURATION CONSTANTS
# ==========================================
# Default Time Speeds (Real Seconds per IC Minute)
# Standard: 1 real min = 4 IC mins => 60 / 4 = 15.0 seconds
# Weekend:  1 real min = 6 IC mins => 60 / 6 = 10.0 seconds
SPEED_STANDARD = 15.0
SPEED_WEEKEND = 10.0

CALIBRATION_FILE = "calibration.json"

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
IC_MIN_PER_DAY = 24 * 60

# Official SchoolRP Weekday Schedule (IC Time)
SCHOOL_SCHEDULE: Dict[str, str] = {
    "Start of Day": "07:30",
    "Breakfast": "08:00",
    "Period 1": "08:30",
    "Period 2": "08:55",
    "Break": "10:35",
    "Period 3": "10:55",
    "Lunch": "12:35",
    "Period 4": "13:20",
    "End of Day": "15:00"
}

def clear_screen():
    """Clears the console screen in a cross-platform way."""
    os.system('cls' if os.name == 'nt' else 'clear')

def time_to_min(time_str: str) -> Optional[int]:
    """
    Converts HH:MM string to total minutes from midnight.
    Returns None if format is invalid.
    """
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

def get_day_index(day_input: str) -> Optional[int]:
    """
    Tries to parse a day index (0-6) from a string input (name, abbreviation, or number).
    Returns None if invalid.
    """
    day_input = day_input.strip().capitalize()
    
    # Check full names
    if day_input in DAYS_OF_WEEK:
        return DAYS_OF_WEEK.index(day_input)
    
    # Check abbreviations (e.g., "Mon", "Thu")
    for i, d in enumerate(DAYS_OF_WEEK):
        if d.startswith(day_input):
            return i
            
    # Check numbers 1-7 (1=Monday)
    try:
        val = int(day_input)
        if 1 <= val <= 7:
            return val - 1
    except ValueError:
        pass
        
    return None

class SchoolRPTimeBoard:
    """
    Manages the calibration, state persistence, and time conversion logic for SchoolRP.
    """
    
    def __init__(self):
        # Format: day_index * 1440 + minutes_into_day
        self.cal_ic_total_min: Optional[float] = None
        self.cal_real_dt: Optional[datetime] = None
        self.time_speed: float = SPEED_STANDARD
        self.load_calibration()

    def load_calibration(self) -> bool:
        """Loads calibration data from a local JSON file."""
        if not os.path.exists(CALIBRATION_FILE):
            return False
            
        try:
            with open(CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
                
                # Migration Logic: 
                # If old format (ic_min present, ic_total_min missing), convert to Monday (0) + min
                if 'ic_min' in data and 'ic_total_min' not in data:
                    self.cal_ic_total_min = float(data['ic_min']) # Default to Monday
                else:
                    self.cal_ic_total_min = data.get('ic_total_min')
                    
                if data.get('real_dt'):
                    self.cal_real_dt = datetime.fromisoformat(data['real_dt'])
                self.time_speed = data.get('time_speed', SPEED_STANDARD)
                return True
        except (json.JSONDecodeError, KeyError, ValueError):
            return False

    def save_calibration(self, ic_time_str: Optional[str] = None, ic_day_idx: Optional[int] = None) -> bool:
        """
        Saves current state to JSON.
        If ic_time_str and ic_day_idx are provided, performs a fresh Sync.
        Otherwise, just saves the current configuration (speed).
        """
        # If performing a full sync
        if ic_time_str and ic_day_idx is not None:
            day_min = time_to_min(ic_time_str)
            if day_min is None:
                return False
                
            self.cal_ic_total_min = (ic_day_idx * IC_MIN_PER_DAY) + day_min
            self.cal_real_dt = datetime.now()
        
        # Prepare data
        data = {
            'ic_total_min': self.cal_ic_total_min,
            'real_dt': self.cal_real_dt.isoformat() if self.cal_real_dt else None,
            'time_speed': self.time_speed
        }
        
        try:
            with open(CALIBRATION_FILE, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except IOError:
            return False

    def get_estimated_ic_now(self) -> Tuple[Optional[str], Optional[str], Optional[float]]:
        """
        Calculates current IC status based on elapsed real time.
        Returns: (Day Name, HH:MM Time, minutes_into_current_day)
        """
        if self.cal_real_dt is None or self.cal_ic_total_min is None:
            return None, None, None
        
        delta_real_seconds = (datetime.now() - self.cal_real_dt).total_seconds()
        delta_ic_minutes = delta_real_seconds / self.time_speed
        
        current_total_min = self.cal_ic_total_min + delta_ic_minutes
        
        # Calculate Day and Time
        total_days = int(current_total_min // IC_MIN_PER_DAY)
        current_day_idx = total_days % 7
        
        minutes_into_day = current_total_min % IC_MIN_PER_DAY
        
        return DAYS_OF_WEEK[current_day_idx], min_to_time(minutes_into_day), minutes_into_day

    def get_ic_time_at(self, real_time_str: str) -> Tuple[Optional[str], Optional[str], Optional[float]]:
        """
        Calculates predicted IC time for a specific real-world HH:MM today.
        Returns: (Day Name, HH:MM Time, minutes_into_current_day)
        """
        if self.cal_real_dt is None or self.cal_ic_total_min is None:
            return None, None, None
            
        now = datetime.now()
        h_m = time_to_min(real_time_str)
        if h_m is None:
            return None, None, None
            
        h, m = h_m // 60, h_m % 60
        target_real_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            
        delta_real_seconds = (target_real_dt - self.cal_real_dt).total_seconds()
        delta_ic_minutes = delta_real_seconds / self.time_speed
        
        current_total_min = self.cal_ic_total_min + delta_ic_minutes
        
        total_days = int(current_total_min // IC_MIN_PER_DAY)
        current_day_idx = total_days % 7
        minutes_into_day = current_total_min % IC_MIN_PER_DAY

        return DAYS_OF_WEEK[current_day_idx], min_to_time(minutes_into_day), minutes_into_day

    def print_board(self, custom_ic_day: Optional[str] = None, custom_ic_min: Optional[float] = None):
        """Displays the dashboard with current IC time and period countdowns."""
        ic_day, ic_str, ic_min = self.get_estimated_ic_now()
        
        # Override for prediction display
        if custom_ic_min is not None and custom_ic_day is not None:
            ic_min = custom_ic_min
            ic_day = custom_ic_day
            ic_str = min_to_time(ic_min)

        if ic_day is None or ic_str is None:
            print("\n[!] No calibration data available.")
            return

        print("\n" + "="*50)
        # Centered Time Display
        time_display = f"{ic_day} {ic_str}"
        print(f" {time_display} ".center(50, "="))
        print(f" Speed: {self.time_speed}s/IC min (1:{60/self.time_speed:.1f}) ".center(50))
        print("="*50)
        
        if self.cal_real_dt:
            sync_time = self.cal_real_dt.strftime('%H:%M:%S')
            print(f" (Last Sync: {sync_time} OOC) ".center(50))
            print("-" * 50)
        
        print(f"{'PERIOD':<20} | {'TIME':<6} | {'REMAINING'}")
        print("-" * 50)
        
        # Detect Weekend
        is_weekend = ic_day in ["Saturday", "Sunday"]
        if is_weekend:
             print(f"{'WEEKEND - NO SCHOOL':^50}")
        else:
            sorted_schedule = sorted(SCHOOL_SCHEDULE.items(), key=lambda x: time_to_min(x[1]) or 0)

            for period, ic_time_str in sorted_schedule:
                period_min = time_to_min(ic_time_str)
                if period_min is None: continue
                
                # Calculate wait time within the day
                ic_wait = period_min - ic_min
                
                if ic_wait < 0:
                     # Period passed for today
                     countdown = "PASSED"
                elif ic_wait < 1:
                     countdown = "NOW"
                else:
                    real_wait_total_sec = ic_wait * self.time_speed
                    h = int(real_wait_total_sec // 3600)
                    m = int((real_wait_total_sec % 3600) // 60)
                    s = int(real_wait_total_sec % 60)
                    countdown = f"{h}h {m}m {s}s"
                    
                print(f"{period:<20} | {ic_time_str:<6} | {countdown}")
                
        print("="*50)

def main():
    board = SchoolRPTimeBoard()
    
    while True:
        try:
            clear_screen()
            print("\n--- SchoolRP OOC Time Dashboard (Day Supported) ---")
            
            if board.cal_real_dt:
                board.print_board()
            else:
                print("\n[!] Dashboard Offline: No Calibration Data.")
                print("Please perform an IC Sync (Option 1) to start.")
            
            print("\n[Menu Options]")
            print("1. [SYNC]    Update Day & Time")
            print("2. [PREDICT] What time will it be at ...?")
            print("3. [REFRESH] Update countdowns")
            print(f"4. [CONFIG]  Change Time Speed (Current: {board.time_speed}s/min)")
            print("q. [QUIT]    Close the dashboard")
            
            choice = input("\nSelect: ").strip().lower()
            
            if choice == '1':
                print("\n--- SYNC WIZARD ---")
                day_str = input("1. Current IC Day (e.g. Mon, Monday, 1): ")
                day_idx = get_day_index(day_str)
                
                if day_idx is None:
                     input("\n[!] Invalid Day. Returns to menu.\n")
                     continue
                     
                ic_time = input(f"2. Current {DAYS_OF_WEEK[day_idx]} Time (HH:MM): ").strip()
                
                if board.save_calibration(ic_time, day_idx):
                    input(f"\n[✓] Sync Successful! Set to {DAYS_OF_WEEK[day_idx]} {ic_time}.\nPress Enter to return.")
                else:
                    input("\n[!] Error: Invalid Time format (HH:MM).\nPress Enter to try again.")
                    
            elif choice == '2':
                ooc = input("\nEnter Target Real (OOC) Time (HH:MM): ").strip()
                day, time, mins = board.get_ic_time_at(ooc)
                if day:
                    print(f"\n>>> At {ooc} OOC, it will be {day} {time} IC.")
                    board.print_board(custom_ic_day=day, custom_ic_min=mins)
                    input("\nPress Enter to return to live dashboard.")
                else:
                    input("\n[!] Error: Invalid format.\nPress Enter to return.")
                    
            elif choice == '3':
                continue 

            elif choice == '4':
                print(f"\n--- Time Speed Configuration ---")
                print(f"1. Standard ({SPEED_STANDARD}s/min) - Default")
                print(f"2. Weekend ({SPEED_WEEKEND}s/min) - Fast")
                print(f"3. Custom")
                
                c = input("\nSelect Speed: ").strip()
                new_speed = None
                
                if c == '1':
                    new_speed = SPEED_STANDARD
                elif c == '2':
                    new_speed = SPEED_WEEKEND
                elif c == '3':
                    try:
                        s = float(input("Enter seconds per IC minute (e.g. 15.0): "))
                        if s > 0:
                            new_speed = s
                        else:
                            print("Speed must be positive.")
                    except ValueError:
                        print("Invalid number.")
                
                if new_speed:
                    board.time_speed = new_speed
                    board.save_calibration() # Save just the config
                    input(f"\n[✓] Speed updated to {new_speed}s/min.\nPress Enter to return.")
                else:
                    input("\n[!] Cancelled or Invalid.\nPress Enter to return.")
                    
            elif choice == 'q':
                print("\nExiting")
                break
        except KeyboardInterrupt:
            print("\nExiting")
            break

if __name__ == "__main__":
    main()

