#!/usr/bin/env python3
"""
Smart Library - Seat Booking System (Auto Refresh 2s)
-----------------------------------------------------
✅ 50 seats (5x10)
✅ Green = Free | Red = Occupied
✅ Click seat → Book (Name, Mobile, Duration, Entry Time)
✅ Auto timer + Auto reset when time ends
✅ Show all current bookings on main screen
✅ Search by seat number
✅ Reset all seats
✅ Auto refresh every 2 seconds
"""

import tkinter as tk
from tkinter import messagebox
import csv
from pathlib import Path
import threading
import time
from datetime import datetime, timedelta

# ------------------ CONFIG ------------------
NUM_SEATS = 50
ROWS, COLS = 5, 10
REFRESH_INTERVAL = 2  # seconds

# ✅ Safe path setup (works in all environments)
try:
    DATA_DIR = Path(__file__).parent
except NameError:
    DATA_DIR = Path.cwd()

BOOKINGS_CSV = DATA_DIR / "bookings.csv"

# ------------------ CSV HANDLERS ------------------
def ensure_csv():
    """Ensure bookings.csv file exists with headers."""
    if not BOOKINGS_CSV.exists():
        with open(BOOKINGS_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["seat_id", "name", "mobile", "duration", "entry_time", "start_time", "status"])

def read_active_bookings():
    """Return a dict of currently active bookings."""
    active = {}
    if BOOKINGS_CSV.exists():
        with open(BOOKINGS_CSV, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["status"] == "Occupied":
                    start = datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M:%S")
                    duration = int(row["duration"])
                    end = start + timedelta(minutes=duration)
                    if datetime.now() < end:
                        active[int(row["seat_id"])] = (end, row["name"], row["mobile"], row["entry_time"])
    return active

def add_booking(seat_id, name, mobile, duration, entry_time):
    """Add or update a booking in the CSV."""
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    if BOOKINGS_CSV.exists():
        with open(BOOKINGS_CSV, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row["seat_id"]) != seat_id:
                    rows.append(row)
    rows.append({
        "seat_id": seat_id,
        "name": name,
        "mobile": mobile,
        "duration": duration,
        "entry_time": entry_time,
        "start_time": start_time,
        "status": "Occupied"
    })
    with open(BOOKINGS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["seat_id", "name", "mobile", "duration", "entry_time", "start_time", "status"])
        writer.writeheader()
        writer.writerows(rows)

def update_booking_status(seat_id, status):
    """Update booking status (Free or Occupied)."""
    rows = []
    if BOOKINGS_CSV.exists():
        with open(BOOKINGS_CSV, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row["seat_id"]) == seat_id:
                    row["status"] = status
                rows.append(row)
    with open(BOOKINGS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["seat_id", "name", "mobile", "duration", "entry_time", "start_time", "status"])
        writer.writeheader()
        writer.writerows(rows)

# ------------------ MAIN APP ------------------
class SmartLibraryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Library - Seat Booking System")
        self.geometry("1200x700")
        self.resizable(False, False)

        self.active = read_active_bookings()
        self.buttons = {}

        self.create_ui()
        self.refresh_ui()
        self.auto_refresh()
        threading.Thread(target=self.auto_reset_thread, daemon=True).start()

    # ------------------ UI LAYOUT ------------------
    def create_ui(self):
        tk.Label(self, text="📚 Smart Library Seat Booking System", font=("Arial", 18, "bold")).pack(pady=10)

        grid_frame = tk.Frame(self)
        grid_frame.pack()

        for r in range(ROWS):
            for c in range(COLS):
                sid = r * COLS + c + 1
                btn = tk.Button(grid_frame, text=f"{sid}", width=12, height=4,
                                 bg="lightgreen", font=("Arial", 10, "bold"),
                                 command=lambda s=sid: self.book_or_reset(s))
                btn.grid(row=r, column=c, padx=5, pady=5)
                self.buttons[sid] = btn

        # Control buttons
        control_frame = tk.Frame(self)
        control_frame.pack(pady=10)
        tk.Button(control_frame, text="🔍 Search Seat", command=self.search_by_seat, bg="#2196F3", fg="white").pack(side="left", padx=5)
        tk.Button(control_frame, text="♻ Reset All Seats", command=self.reset_all, bg="#f44336", fg="white").pack(side="left", padx=5)

        # Booking display
        tk.Label(self, text="📋 Current Active Bookings", font=("Arial", 14, "bold")).pack(pady=10)
        self.text_box = tk.Text(self, height=15, width=80, font=("Courier", 10))
        self.text_box.pack()
        self.refresh_booking_list()

    # ------------------ BUTTON LOGIC ------------------
    def book_or_reset(self, seat_id):
        if seat_id in self.active:
            if messagebox.askyesno("Reset", f"Seat {seat_id} is occupied. Reset it?"):
                self.reset_seat(seat_id)
        else:
            self.book_seat(seat_id)

    def book_seat(self, seat_id):
        popup = tk.Toplevel(self)
        popup.title(f"Book Seat {seat_id}")
        popup.geometry("350x300")

        tk.Label(popup, text=f"Booking Seat {seat_id}", font=("Arial", 12, "bold")).pack(pady=10)
        fields = ["Name", "Mobile", "Duration (min)", "Entry Time (HH:MM 24hr)"]
        entries = {}

        for f in fields:
            tk.Label(popup, text=f).pack()
            e = tk.Entry(popup)
            e.pack(pady=3)
            if "Entry" in f:
                e.insert(0, datetime.now().strftime("%H:%M"))
            entries[f] = e

        def confirm():
            try:
                name = entries["Name"].get().strip()
                mobile = entries["Mobile"].get().strip()
                duration = int(entries["Duration (min)"].get().strip())
                entry_time = entries["Entry Time (HH:MM 24hr)"].get().strip()
                if not name or not mobile or not entry_time:
                    raise ValueError
            except:
                messagebox.showerror("Error", "Invalid input.")
                return

            add_booking(seat_id, name, mobile, duration, entry_time)
            self.active = read_active_bookings()
            self.refresh_ui()
            self.refresh_booking_list()
            popup.destroy()
            messagebox.showinfo("Booked", f"Seat {seat_id} booked for {duration} mins.")

        tk.Button(popup, text="Confirm Booking", command=confirm, bg="#4CAF50", fg="white").pack(pady=10)
        tk.Button(popup, text="Cancel", command=popup.destroy).pack()

    # ------------------ AUTO / RESET ------------------
    def reset_seat(self, seat_id):
        update_booking_status(seat_id, "Free")
        self.active.pop(seat_id, None)
        self.refresh_ui()
        self.refresh_booking_list()

    def reset_all(self):
        if messagebox.askyesno("Confirm", "Are you sure to reset ALL seats?"):
            ensure_csv()  # recreate CSV with header
            self.active.clear()
            self.refresh_ui()
            self.refresh_booking_list()
            messagebox.showinfo("Reset", "All seats reset successfully!")

    def auto_reset_thread(self):
        """Thread to auto-free expired seats."""
        while True:
            now = datetime.now()
            for seat_id, (end, name, mobile, etime) in list(self.active.items()):
                if now >= end:
                    update_booking_status(seat_id, "Free")
                    self.active.pop(seat_id, None)
                    self.after(0, lambda s=seat_id, n=name: messagebox.showinfo("Time Over", f"Seat {s} ({n}) time ended."))
                    self.after(0, self.refresh_ui)
                    self.after(0, self.refresh_booking_list)
            time.sleep(1)

    # ------------------ REFRESH ------------------
    def refresh_ui(self):
        self.active = read_active_bookings()
        for sid, btn in self.buttons.items():
            if sid in self.active:
                end, name, mobile, etime = self.active[sid]
                left = int((end - datetime.now()).total_seconds() // 60)
                btn.config(bg="red", text=f"{sid}\n{name}\n{left}m left")
            else:
                btn.config(bg="lightgreen", text=f"{sid}")
        self.refresh_booking_list()

    def refresh_booking_list(self):
        self.text_box.config(state="normal")
        self.text_box.delete("1.0", tk.END)
        active = read_active_bookings()
        if active:
            now = datetime.now()
            self.text_box.insert(tk.END, f"{'Seat':<6}{'Name':<15}{'Mobile':<15}{'Entry':<10}{'Left':<10}\n")
            self.text_box.insert(tk.END, "-"*60 + "\n")
            for sid, (end, name, mobile, etime) in active.items():
                left = int((end - now).total_seconds() // 60)
                self.text_box.insert(tk.END, f"{sid:<6}{name:<15}{mobile:<15}{etime:<10}{left}m\n")
        else:
            self.text_box.insert(tk.END, "No active bookings.\n")
        self.text_box.config(state="disabled")

    def auto_refresh(self):
        self.refresh_ui()
        self.after(REFRESH_INTERVAL * 1000, self.auto_refresh)

    # ------------------ SEARCH ------------------
    def search_by_seat(self):
        popup = tk.Toplevel(self)
        popup.title("Search Booking")
        popup.geometry("300x150")

        tk.Label(popup, text="Enter Seat Number (1–50):").pack(pady=5)
        entry = tk.Entry(popup)
        entry.pack(pady=5)
        result = tk.Label(popup, text="", font=("Arial", 10))
        result.pack(pady=5)

        def search():
            try:
                sid = int(entry.get())
                if sid < 1 or sid > NUM_SEATS:
                    raise ValueError
            except:
                messagebox.showerror("Error", "Enter a valid seat number (1–50).")
                return
            booking = read_active_bookings().get(sid)
            if booking:
                end, name, mobile, etime = booking
                mins = int((end - datetime.now()).total_seconds() // 60)
                result.config(text=f"Seat {sid} is OCCUPIED\n{name}, {mobile}\nEntry: {etime}\nLeft: {mins}m")
            else:
                result.config(text=f"Seat {sid} is FREE")

        tk.Button(popup, text="Search", command=search, bg="#2196F3", fg="white").pack(pady=5)

# ------------------ RUN ------------------
if __name__ == "__main__":
    ensure_csv()
    app = SmartLibraryApp()
    app.mainloop()