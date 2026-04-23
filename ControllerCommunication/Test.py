import tkinter as tk
from tkinter import scrolledtext
import threading
import time
from SerialRW.SerialRW import serial_read, serial_write
from ControllerCom.ControllerCom import makeCommandData

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Monitor & Controller")
        
        # Initialize your serial script
        # Change 'COM3' to your actual port
        self.serial_tool = SerialHandler('COM3', 9600)

        # --- UI LAYOUT ---
        
        # Top Section: Input
        tk.Label(root, text="Step Count:").grid(row=0, column=0, padx=10, pady=10)
        self.entry = tk.Entry(root)
        self.entry.grid(row=0, column=1, padx=10, pady=10)
        
        self.send_btn = tk.Button(root, text="Send", command=self.handle_send)
        self.send_btn.grid(row=0, column=2, padx=10, pady=10)

        # Bottom Section: Monitor
        tk.Label(root, text="Incoming Serial Stream:").grid(row=1, column=0, sticky="w", padx=10)
        self.monitor = scrolledtext.ScrolledText(root, width=50, height=15)
        self.monitor.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

        # --- BACKGROUND THREAD ---
        # This thread constantly checks for new serial data
        self.running = True
        self.thread = threading.Thread(target=self.monitor_serial, daemon=True)
        self.thread.start()

    def handle_send(self):
        try:
            val = int(self.entry.get())
            # Call your function that returns the confirmation string
            log_msg = self.serial_tool.serial_write(val)
            self.update_monitor(f"[OUT] {log_msg}")
        except ValueError:
            self.update_monitor("[ERROR] Please enter a valid integer")

    def update_monitor(self, text):
        """Safely appends text to the monitor."""
        self.monitor.insert(tk.END, text + "\n")
        self.monitor.see(tk.END) # Auto-scroll to bottom

    def monitor_serial(self):
        """Background loop to catch incoming data."""
        while self.running:
            incoming = self.serial_tool.read_incoming()
            if incoming:
                # Use 'after' to safely update GUI from a different thread
                self.root.after(0, self.update_monitor, f"[IN] {incoming}")
            time.sleep(0.01) # Small sleep to prevent CPU spiking

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()