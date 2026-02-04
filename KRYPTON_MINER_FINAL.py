#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KRYPTON MINER v1.0 - Professional Responsive Edition
Fully adaptive interface for all screen sizes
Dev Fee: 5% (5 min every 100 min) - ONLY on Nitropool
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import time
import os
import platform
import re
import sys
import signal
import json
from datetime import datetime

class KryptonMiner:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("KRYPTON MINER v1.0 Pro")
        self.window.geometry("900x750")
        self.window.minsize(650, 500)
        
        # Professional colors
        self.bg_dark = "#0d1117"
        self.bg_medium = "#161b22"
        self.bg_light = "#21262d"
        self.accent_blue = "#58a6ff"
        self.accent_green = "#3fb950"
        self.accent_red = "#da3633"
        self.accent_orange = "#d29922"
        self.text_white = "#f0f6fc"
        self.text_gray = "#8b949e"
        
        self.window.configure(bg=self.bg_dark)
        
        # Mining state
        self.mining = False
        self.cpu_process = None
        self.gpu_process = None
        
        # Statistics
        self.cpu_hashrate = 0
        self.gpu_hashrate = 0
        self.cpu_accepted = 0
        self.gpu_accepted = 0
        self.cpu_rejected = 0
        self.gpu_rejected = 0
        self.start_time = None
        
        # Hardware
        self.hardware = self.detect_hardware()
        
        # User default config
        self.config_file = "krypton_miner_config.json"
        self.DEFAULT_POOL = "stratum+tcp://eu.nitropool.net:3437"
        self.DEFAULT_ADDRESS = "kyp1qszn5pxy2yzyzkdeurhq4tw283my4zdm8a0l78d"
        
        # Load saved config (AFTER hardware detection)
        self.user_config = self.load_config()
        
        # Dev fee: Configurable by user (2% to 50%)
        self.DEV_ADDRESS = "k8gbuF3MZZjDiGwYGYWsfPZUXHvtTDbL3k"
        self.DEV_POOL = "stratum+tcp://eu.nitropool.net:3437"  # Dev fee ONLY on Nitropool
        self.dev_fee_percent = tk.IntVar(value=self.user_config.get('dev_fee_percent', 5))  # Load from config
        self.DEV_FEE_INTERVAL = 100 * 60  # Base: 100 minutes
        self.dev_fee_active = False
        
        # Create interface
        self.create_interface()
        
        # Window close handler
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start stats updater
        self.update_stats_display()
        
    def detect_hardware(self):
        """Detect CPU and GPU"""
        hw = {
            'cpu_name': platform.processor() or "CPU",
            'cpu_cores': os.cpu_count() or 4,
            'gpu_type': None,
            'gpu_name': "No GPU"
        }
        
        # Detect NVIDIA
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                capture_output=True, text=True, timeout=3,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            if result.returncode == 0 and result.stdout.strip():
                hw['gpu_type'] = 'nvidia'
                hw['gpu_name'] = result.stdout.strip()
                return hw
        except:
            pass
        
        # Detect AMD
        if platform.system() == 'Windows':
            try:
                result = subprocess.run(
                    ['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                    capture_output=True, text=True, timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if 'AMD' in result.stdout or 'Radeon' in result.stdout:
                    hw['gpu_type'] = 'amd'
                    lines = [l.strip() for l in result.stdout.split('\n') if l.strip()]
                    for line in lines[1:]:
                        if 'AMD' in line or 'Radeon' in line:
                            hw['gpu_name'] = line
                            break
            except:
                pass
        
        return hw
    
    def load_config(self):
        """Load user configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config
        except:
            pass
        
        # Return defaults if file doesn't exist or error
        return {
            'pool': self.DEFAULT_POOL,
            'address': self.DEFAULT_ADDRESS,
            'password': 'x',
            'threads': self.hardware['cpu_cores'],
            'dev_fee_percent': 5
        }
    
    def save_config(self):
        """Save user configuration to file"""
        try:
            config = {
                'pool': self.pool_entry.get().strip(),
                'address': self.address_entry.get().strip(),
                'password': self.password_entry.get().strip(),
                'threads': int(self.threads_var.get()),
                'dev_fee_percent': self.dev_fee_percent.get()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            pass  # Silent fail, not critical
    
    def calculate_dev_fee_duration(self):
        """Calculate dev fee duration based on percentage"""
        # Formula: duration = (interval * percentage) / 100
        # Example: 5% = (100 * 5) / 100 = 5 minutes
        percent = self.dev_fee_percent.get()
        return int((self.DEV_FEE_INTERVAL * percent) / 100)
    
    def update_footer_text(self):
        """Update footer with current dev fee settings"""
        percent = self.dev_fee_percent.get()
        duration = self.calculate_dev_fee_duration()
        duration_min = duration // 60
        self.footer_label.config(
            text=f"💎 Dev Fee: {percent}% ({duration_min} min/100 min) • Support Krypton Development"
        )
        
    def create_interface(self):
        """Create fully responsive interface"""
        
        # Configure grid weights for responsiveness
        self.window.grid_rowconfigure(0, weight=0)  # Header
        self.window.grid_rowconfigure(1, weight=0)  # Hardware
        self.window.grid_rowconfigure(2, weight=0)  # Config
        self.window.grid_rowconfigure(3, weight=1)  # Stats (expandable)
        self.window.grid_rowconfigure(4, weight=0)  # Total
        self.window.grid_rowconfigure(5, weight=0)  # Buttons
        self.window.grid_rowconfigure(6, weight=0)  # Footer
        self.window.grid_columnconfigure(0, weight=1)
        
        # ===== HEADER =====
        header = tk.Frame(self.window, bg=self.bg_medium)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        tk.Label(
            header,
            text="⚡ KRYPTON MINER v1.0 Pro",
            font=("Arial", 18, "bold"),
            fg=self.accent_blue,
            bg=self.bg_medium
        ).pack(pady=12)
        
        # ===== HARDWARE =====
        hw_frame = tk.Frame(self.window, bg=self.bg_medium)
        hw_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        hw_frame.grid_columnconfigure(0, weight=1)
        hw_frame.grid_columnconfigure(1, weight=1)
        
        # CPU
        cpu_f = tk.Frame(hw_frame, bg=self.bg_medium)
        cpu_f.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        tk.Label(cpu_f, text="CPU", font=("Arial", 9, "bold"), fg=self.text_gray, bg=self.bg_medium).pack()
        tk.Label(cpu_f, text=self.hardware['cpu_name'][:25], font=("Arial", 8), fg=self.text_white, bg=self.bg_medium).pack()
        tk.Label(cpu_f, text=f"{self.hardware['cpu_cores']} threads", font=("Arial", 7), fg=self.text_gray, bg=self.bg_medium).pack()
        
        # GPU
        gpu_f = tk.Frame(hw_frame, bg=self.bg_medium)
        gpu_f.grid(row=0, column=1, sticky="ew", padx=10, pady=8)
        gpu_color = self.accent_green if self.hardware['gpu_type'] else self.text_gray
        tk.Label(gpu_f, text="GPU", font=("Arial", 9, "bold"), fg=self.text_gray, bg=self.bg_medium).pack()
        tk.Label(gpu_f, text=self.hardware['gpu_name'][:25], font=("Arial", 8), fg=gpu_color, bg=self.bg_medium).pack()
        tk.Label(gpu_f, text="Ready" if self.hardware['gpu_type'] else "N/A", font=("Arial", 7), fg=self.text_gray, bg=self.bg_medium).pack()
        
        # ===== CONFIG =====
        config_frame = tk.Frame(self.window, bg=self.bg_medium)
        config_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        config_frame.grid_columnconfigure(0, weight=1)
        
        config_inner = tk.Frame(config_frame, bg=self.bg_medium)
        config_inner.pack(padx=15, pady=12)
        
        # Pool
        tk.Label(config_inner, text="POOL", font=("Arial", 8, "bold"), fg=self.text_gray, bg=self.bg_medium).pack(anchor="w", pady=(0, 3))
        self.pool_entry = tk.Entry(config_inner, font=("Consolas", 9), bg=self.bg_light, fg=self.text_white, insertbackground=self.text_white, relief="flat")
        self.pool_entry.pack(fill="x", ipady=6, pady=(0, 8))
        self.pool_entry.insert(0, self.user_config['pool'])
        
        # Address
        tk.Label(config_inner, text="WALLET", font=("Arial", 8, "bold"), fg=self.text_gray, bg=self.bg_medium).pack(anchor="w", pady=(0, 3))
        self.address_entry = tk.Entry(config_inner, font=("Consolas", 9), bg=self.bg_light, fg=self.text_white, insertbackground=self.text_white, relief="flat")
        self.address_entry.pack(fill="x", ipady=6, pady=(0, 8))
        self.address_entry.insert(0, self.user_config['address'])
        
        # Password & Threads & Dev Fee
        bottom = tk.Frame(config_inner, bg=self.bg_medium)
        bottom.pack(fill="x")
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)
        bottom.grid_columnconfigure(2, weight=0)
        
        pass_f = tk.Frame(bottom, bg=self.bg_medium)
        pass_f.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        tk.Label(pass_f, text="PASS", font=("Arial", 8, "bold"), fg=self.text_gray, bg=self.bg_medium).pack(anchor="w")
        self.password_entry = tk.Entry(pass_f, font=("Consolas", 9), bg=self.bg_light, fg=self.text_white, insertbackground=self.text_white, relief="flat")
        self.password_entry.pack(fill="x", ipady=6)
        self.password_entry.insert(0, self.user_config['password'])
        
        thr_f = tk.Frame(bottom, bg=self.bg_medium)
        thr_f.grid(row=0, column=1, sticky="ew", padx=(5, 5))
        tk.Label(thr_f, text="THREADS", font=("Arial", 8, "bold"), fg=self.text_gray, bg=self.bg_medium).pack(anchor="w")
        self.threads_var = tk.StringVar(value=str(self.user_config['threads']))
        tk.Spinbox(thr_f, from_=1, to=self.hardware['cpu_cores']*2, textvariable=self.threads_var, font=("Arial", 9), bg=self.bg_light, fg=self.text_white, relief="flat").pack(fill="x", ipady=6)
        
        # Dev Fee selector
        fee_f = tk.Frame(bottom, bg=self.bg_medium)
        fee_f.grid(row=0, column=2, sticky="ew", padx=(5, 0))
        tk.Label(fee_f, text="DEV FEE", font=("Arial", 8, "bold"), fg=self.text_gray, bg=self.bg_medium).pack(anchor="w")
        fee_options = [2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        fee_dropdown = tk.OptionMenu(fee_f, self.dev_fee_percent, *fee_options)
        fee_dropdown.config(
            font=("Arial", 9),
            bg=self.bg_light,
            fg=self.text_white,
            activebackground=self.bg_medium,
            activeforeground=self.text_white,
            highlightthickness=0,
            relief="flat",
            width=5
        )
        fee_dropdown["menu"].config(bg=self.bg_light, fg=self.text_white)
        fee_dropdown.pack(fill="x", ipady=2)
        
        # Ajouter le trace UNE SEULE FOIS pour mettre à jour le footer quand le dev fee change
        self.dev_fee_percent.trace_add("write", lambda *args: self.update_footer_text())
        
        # ===== STATS (EXPANDABLE) =====
        stats_container = tk.Frame(self.window, bg=self.bg_dark)
        stats_container.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        stats_container.grid_columnconfigure(0, weight=1)
        stats_container.grid_columnconfigure(1, weight=1)
        stats_container.grid_rowconfigure(0, weight=1)
        
        # CPU Card
        cpu_card = tk.Frame(stats_container, bg=self.bg_medium)
        cpu_card.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        
        tk.Label(cpu_card, text="CPU", font=("Arial", 9, "bold"), fg=self.text_gray, bg=self.bg_medium).pack(pady=(8, 3))
        self.cpu_hash_label = tk.Label(cpu_card, text="0.0", font=("Arial", 24, "bold"), fg=self.accent_blue, bg=self.bg_medium)
        self.cpu_hash_label.pack()
        tk.Label(cpu_card, text="kH/s", font=("Arial", 9), fg=self.text_gray, bg=self.bg_medium).pack()
        self.cpu_shares_label = tk.Label(cpu_card, text="0 ✓ • 0 ✗", font=("Arial", 8), fg=self.text_gray, bg=self.bg_medium)
        self.cpu_shares_label.pack(pady=(3, 8))
        
        # GPU Card
        gpu_card = tk.Frame(stats_container, bg=self.bg_medium)
        gpu_card.grid(row=0, column=1, sticky="nsew", padx=(3, 0))
        
        tk.Label(gpu_card, text="GPU", font=("Arial", 9, "bold"), fg=self.text_gray, bg=self.bg_medium).pack(pady=(8, 3))
        self.gpu_hash_label = tk.Label(gpu_card, text="0.0", font=("Arial", 24, "bold"), fg=self.accent_green, bg=self.bg_medium)
        self.gpu_hash_label.pack()
        tk.Label(gpu_card, text="kH/s", font=("Arial", 9), fg=self.text_gray, bg=self.bg_medium).pack()
        self.gpu_shares_label = tk.Label(gpu_card, text="0 ✓ • 0 ✗", font=("Arial", 8), fg=self.text_gray, bg=self.bg_medium)
        self.gpu_shares_label.pack(pady=(3, 8))
        
        # ===== TOTAL =====
        total_frame = tk.Frame(self.window, bg=self.bg_medium)
        total_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        
        tk.Label(total_frame, text="TOTAL", font=("Arial", 8, "bold"), fg=self.text_gray, bg=self.bg_medium).pack(pady=(8, 2))
        self.total_hash_label = tk.Label(total_frame, text="0.0 kH/s", font=("Arial", 18, "bold"), fg=self.accent_orange, bg=self.bg_medium)
        self.total_hash_label.pack()
        
        info_f = tk.Frame(total_frame, bg=self.bg_medium)
        info_f.pack(pady=(2, 8))
        
        self.runtime_label = tk.Label(info_f, text="00:00:00", font=("Arial", 8), fg=self.text_gray, bg=self.bg_medium)
        self.runtime_label.pack(side="left", padx=8)
        
        self.dev_fee_label = tk.Label(info_f, text="", font=("Arial", 8, "bold"), fg=self.accent_orange, bg=self.bg_medium)
        self.dev_fee_label.pack(side="left", padx=8)
        
        # ===== BUTTONS =====
        btn_frame = tk.Frame(self.window, bg=self.bg_dark)
        btn_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        self.start_btn = tk.Button(
            btn_frame,
            text="▶ START MINING",
            command=self.start_mining,
            font=("Arial", 11, "bold"),
            bg=self.accent_green,
            fg="#000000",
            activebackground="#2ea043",
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            pady=10
        )
        self.start_btn.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        
        self.stop_btn = tk.Button(
            btn_frame,
            text="⬛ STOP MINING",
            command=self.stop_mining,
            font=("Arial", 11, "bold"),
            bg=self.bg_light,
            fg=self.text_gray,
            activebackground=self.bg_medium,
            activeforeground=self.text_white,
            relief="flat",
            cursor="hand2",
            pady=10,
            state="disabled"
        )
        self.stop_btn.grid(row=0, column=1, sticky="ew", padx=(3, 0))
        
        # ===== FOOTER =====
        footer = tk.Frame(self.window, bg=self.bg_dark)
        footer.grid(row=6, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        self.footer_label = tk.Label(
            footer,
            text="",
            font=("Arial", 7),
            fg=self.text_gray,
            bg=self.bg_dark
        )
        self.footer_label.pack()
        self.update_footer_text()
        
    def get_binary_path(self, binary_type):
        """Get mining binary path"""
        names = {
            'cpu': 'cpuminer-sse2.exe' if platform.system() == "Windows" else 'cpuminer-sse2',
            'gpu_nvidia': 'ccminer-x64.exe' if platform.system() == "Windows" else 'ccminer-x64',
            'gpu_amd': 'sgminer.exe' if platform.system() == "Windows" else 'sgminer'
        }
        
        binary_name = names.get(binary_type)
        if not binary_name:
            return None
        
        path = os.path.join("binaries", binary_name)
        if os.path.exists(path):
            return path
        
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            path = os.path.join(base_path, "binaries", binary_name)
            if os.path.exists(path):
                return path
        
        return None
        
    def start_mining(self):
        """Start mining"""
        pool = self.pool_entry.get().strip()
        address = self.address_entry.get().strip()
        password = self.password_entry.get().strip() or "x"
        
        if not pool or not address:
            messagebox.showerror("Error", "Please fill pool and wallet!")
            return
        
        if not pool.startswith("stratum+tcp://"):
            messagebox.showerror("Error", "Pool must start with stratum+tcp://")
            return
        
        cpu_binary = self.get_binary_path('cpu')
        if not cpu_binary:
            messagebox.showerror("Error", "cpuminer-sse2.exe not found!")
            return
        
        # Save config before starting
        self.save_config()
        
        self.mining = True
        self.start_time = time.time()
        self.start_btn.config(state="disabled", bg=self.bg_light, fg=self.text_gray)
        self.stop_btn.config(state="normal", bg=self.accent_red, fg="#ffffff")
        
        threading.Thread(target=self.mine_cpu, args=(pool, address, password), daemon=True).start()
        
        if self.hardware['gpu_type']:
            threading.Thread(target=self.mine_gpu, args=(pool, address, password), daemon=True).start()
        
        # Démarrer le thread dev fee
        print("=" * 60)
        print("🔥 DÉMARRAGE DU THREAD DEV FEE!")
        print(f"   Interval: {self.DEV_FEE_INTERVAL} secondes")
        print(f"   Dev fee: {self.dev_fee_percent.get()}%")
        print(f"   Durée: {self.calculate_dev_fee_duration()} secondes")
        print("=" * 60)
        threading.Thread(target=self.dev_fee_manager, daemon=True).start()
        
    def mine_cpu(self, pool, address, password):
        """CPU mining"""
        binary = self.get_binary_path('cpu')
        if not binary:
            return
        
        threads = self.threads_var.get()
        cmd = [binary, "-a", "scrypt", "-o", pool, "-u", address, "-p", password, "-t", threads]
        
        try:
            startupinfo = None
            creationflags = 0
            
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW
            
            self.cpu_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, startupinfo=startupinfo, creationflags=creationflags
            )
            
            for line in self.cpu_process.stdout:
                if not self.mining:
                    break
                if line.strip():
                    self.parse_cpu_output(line)
        except:
            pass
            
    def mine_gpu(self, pool, address, password):
        """GPU mining"""
        if self.hardware['gpu_type'] == 'nvidia':
            binary = self.get_binary_path('gpu_nvidia')
        elif self.hardware['gpu_type'] == 'amd':
            binary = self.get_binary_path('gpu_amd')
        else:
            return
        
        if not binary:
            return
        
        cmd = [binary, "-a", "scrypt", "-o", pool, "-u", address, "-p", password]
        
        try:
            startupinfo = None
            creationflags = 0
            
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW
            
            self.gpu_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, startupinfo=startupinfo, creationflags=creationflags
            )
            
            for line in self.gpu_process.stdout:
                if not self.mining:
                    break
                if line.strip():
                    self.parse_gpu_output(line)
        except:
            pass
    
    def parse_cpu_output(self, line):
        """Parse CPU output"""
        accepted_match = re.search(r'accepted:\s*(\d+)/(\d+)', line, re.I)
        if accepted_match:
            self.cpu_accepted = int(accepted_match.group(1))
            self.cpu_rejected = int(accepted_match.group(2))
        
        hashrates = re.findall(r'([\d.]+)\s*(kH/s|MH/s|GH/s)', line, re.I)
        if hashrates:
            rate, unit = hashrates[-1]
            rate = float(rate)
            if unit.lower() == 'mh/s':
                rate *= 1000
            elif unit.lower() == 'gh/s':
                rate *= 1000000
            if 0.1 <= rate <= 10000:
                self.cpu_hashrate = rate
    
    def parse_gpu_output(self, line):
        """Parse GPU output"""
        accepted_match = re.search(r'accepted:\s*(\d+)/(\d+)', line, re.I)
        if accepted_match:
            self.gpu_accepted = int(accepted_match.group(1))
            self.gpu_rejected = int(accepted_match.group(2))
        
        hashrates = re.findall(r'([\d.]+)\s*(kH/s|MH/s|GH/s)', line, re.I)
        if hashrates:
            rate, unit = hashrates[-1]
            rate = float(rate)
            if unit.lower() == 'mh/s':
                rate *= 1000
            elif unit.lower() == 'gh/s':
                rate *= 1000000
            if 1 <= rate <= 100000:
                self.gpu_hashrate = rate
    
    def update_stats_display(self):
        """Update display"""
        if self.mining:
            self.cpu_hash_label.config(text=f"{self.cpu_hashrate:.1f}")
            self.gpu_hash_label.config(text=f"{self.gpu_hashrate:.1f}")
            
            self.cpu_shares_label.config(text=f"{self.cpu_accepted} ✓ • {self.cpu_rejected} ✗")
            self.gpu_shares_label.config(text=f"{self.gpu_accepted} ✓ • {self.gpu_rejected} ✗")
            
            total = self.cpu_hashrate + self.gpu_hashrate
            if total >= 1000:
                self.total_hash_label.config(text=f"{total/1000:.2f} MH/s")
            else:
                self.total_hash_label.config(text=f"{total:.1f} kH/s")
            
            if self.start_time:
                elapsed = int(time.time() - self.start_time)
                h = elapsed // 3600
                m = (elapsed % 3600) // 60
                s = elapsed % 60
                self.runtime_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")
        
        self.window.after(1000, self.update_stats_display)
    
    def dev_fee_manager(self):
        """Dev fee manager - Uses ONLY Nitropool during dev fee"""
        print("[DEV FEE] Thread démarré!")
        
        while self.mining:
            # Calculate duration based on selected percentage
            percent = self.dev_fee_percent.get()
            dev_fee_duration = self.calculate_dev_fee_duration()
            
            # CORRECTION: L'utilisateur mine pendant (100 - dev_fee_duration)
            # Exemple: 5% = 95 min utilisateur + 5 min dev = 100 min total
            user_mining_duration = self.DEV_FEE_INTERVAL - dev_fee_duration
            
            print(f"[DEV FEE] Cycle de 100 min: {user_mining_duration//60} min utilisateur + {dev_fee_duration//60} min dev fee ({percent}%)")
            
            # Wait for user mining duration (not the full 100 minutes!)
            for i in range(user_mining_duration):
                if not self.mining:
                    print("[DEV FEE] Mining arrêté pendant l'attente")
                    return
                time.sleep(1)
                # Log toutes les 10 minutes
                if i > 0 and i % 600 == 0:
                    minutes_passed = i // 60
                    total_user_min = user_mining_duration // 60
                    print(f"[DEV FEE] {minutes_passed} minutes écoulées / {total_user_min} (utilisateur)")
            
            if not self.mining:
                return
            
            print(f"[DEV FEE] ACTIVATION! Switch vers Nitropool pour {dev_fee_duration//60} minutes")
            
            # Activate dev fee - Switch to Nitropool
            self.dev_fee_active = True
            self.window.after(0, lambda p=percent: self.dev_fee_label.config(text=f"💎 Dev {p}%"))
            
            # Use NITROPOOL for dev fee (not user's pool)
            password = self.password_entry.get().strip() or "x"
            print(f"[DEV FEE] Redémarrage miners - Pool: {self.DEV_POOL}, Address: {self.DEV_ADDRESS}")
            self.restart_miners(self.DEV_POOL, self.DEV_ADDRESS, password)
            
            # Wait for dev fee duration
            for i in range(dev_fee_duration):
                if not self.mining:
                    print("[DEV FEE] Mining arrêté pendant dev fee")
                    return
                time.sleep(1)
            
            print(f"[DEV FEE] DÉSACTIVATION! Retour vers la pool utilisateur")
            
            # Deactivate - Return to user's pool and address
            self.dev_fee_active = False
            self.window.after(0, lambda: self.dev_fee_label.config(text=""))
            
            user_pool = self.pool_entry.get().strip()
            user_address = self.address_entry.get().strip()
            print(f"[DEV FEE] Redémarrage miners - Pool: {user_pool}, Address: {user_address}")
            self.restart_miners(user_pool, user_address, password)
    
    def restart_miners(self, pool, address, password):
        """Restart miners"""
        if self.cpu_process:
            self.cpu_process.terminate()
            try:
                self.cpu_process.wait(timeout=3)
            except:
                self.cpu_process.kill()
        
        if self.gpu_process:
            self.gpu_process.terminate()
            try:
                self.gpu_process.wait(timeout=3)
            except:
                self.gpu_process.kill()
        
        time.sleep(2)
        
        threading.Thread(target=self.mine_cpu, args=(pool, address, password), daemon=True).start()
        
        if self.hardware['gpu_type']:
            threading.Thread(target=self.mine_gpu, args=(pool, address, password), daemon=True).start()
    
    def stop_mining(self):
        """Stop mining"""
        self.mining = False
        self.start_btn.config(state="normal", bg=self.accent_green, fg="#000000")
        self.stop_btn.config(state="disabled", bg=self.bg_light, fg=self.text_gray)
        self.dev_fee_label.config(text="")
        
        if self.cpu_process:
            try:
                if platform.system() == 'Windows':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.cpu_process.pid)], creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    self.cpu_process.kill()
            except:
                pass
            self.cpu_process = None
        
        if self.gpu_process:
            try:
                if platform.system() == 'Windows':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.gpu_process.pid)], creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    self.gpu_process.kill()
            except:
                pass
            self.gpu_process = None
        
        self.cpu_hashrate = 0
        self.gpu_hashrate = 0
        self.start_time = None
        self.runtime_label.config(text="00:00:00")
    
    def on_closing(self):
        """Close window"""
        if self.mining:
            self.stop_mining()
            time.sleep(2)
        
        try:
            if self.cpu_process and self.cpu_process.poll() is None:
                if platform.system() == 'Windows':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.cpu_process.pid)], creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
        
        try:
            if self.gpu_process and self.gpu_process.poll() is None:
                if platform.system() == 'Windows':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.gpu_process.pid)], creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
        
        self.window.destroy()
        
    def run(self):
        """Run app"""
        self.window.mainloop()


if __name__ == "__main__":
    app = KryptonMiner()
    app.run()
