#!/usr/bin/env python3
import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import requests
import re

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U", pkg])

print("Installing dependencies...")
try:
    import yt_dlp
except:
    install("yt-dlp")
    import yt_dlp

try:
    import requests
except:
    install("requests")
    import requests

print("Ready!")

class Downloader:
    def __init__(self):
        self.downloading = False
    
    def detect_platform(self, url):
        if 'snapchat.com' in url or 'snap.com' in url or 't.snapchat.com' in url:
            return 'Snapchat'
        elif 'instagram.com' in url:
            return 'Instagram'
        elif 'tiktok.com' in url:
            return 'TikTok'
        return 'Unknown'
    
    def download_tiktok_api(self, url, folder, status, progress):
        """Download TikTok using alternative API method"""
        try:
            status.config(text="Extracting TikTok video...")
            progress['value'] = 30
            
            # Extract video ID from URL
            video_id = None
            if '/video/' in url:
                video_id = url.split('/video/')[1].split('?')[0].split('/')[0]
            
            if not video_id:
                return False
            
            # Try TikTok API
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            
            # Method 1: Try direct download
            api_url = f"https://www.tiktok.com/oembed?url={url}"
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                title = data.get('title', 'tiktok_video')
                # Clean title
                title = re.sub(r'[<>:"/\\|?*]', '', title)[:50]
                
                progress['value'] = 60
                status.config(text="Downloading TikTok video...")
                
                # Try to get video URL
                video_url = data.get('thumbnail_url', '').replace('_thumbnail', '')
                
                if video_url:
                    video_response = requests.get(video_url, headers=headers, stream=True, timeout=30)
                    if video_response.status_code == 200:
                        filename = os.path.join(folder, f"{title}.mp4")
                        with open(filename, 'wb') as f:
                            for chunk in video_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        progress['value'] = 100
                        return True
            
            return False
            
        except Exception as e:
            print(f"TikTok API method failed: {e}")
            return False
    
    def download_tiktok_ytdlp(self, url, folder, status, progress):
        """Download TikTok using yt-dlp with updated settings"""
        try:
            status.config(text="Using yt-dlp for TikTok...")
            progress['value'] = 20
            
            def hook(d):
                if d['status'] == 'downloading':
                    try:
                        p = d.get('_percent_str', '0%').replace('%','')
                        progress['value'] = float(p)
                        status.config(text=f"Downloading {p}%")
                    except:
                        pass
                elif d['status'] == 'finished':
                    status.config(text="Processing...")
                    progress['value'] = 95
            
            opts = {
                'format': 'best',
                'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
                'progress_hooks': [hook],
                'quiet': True,
                'no_warnings': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://www.tiktok.com/',
                }
            }
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            
            return True
            
        except Exception as e:
            print(f"TikTok yt-dlp failed: {e}")
            return False
    
    def download(self, url, folder, status, progress, platform_lbl):
        if self.downloading:
            messagebox.showwarning("Wait", "Download in progress")
            return
        
        platform = self.detect_platform(url)
        if platform == 'Unknown':
            messagebox.showerror("Error", "Please enter valid Snapchat, Instagram, or TikTok URL")
            return
        
        platform_lbl.config(text=f"Platform: {platform}")
        self.downloading = True
        status.config(text="Starting download...")
        progress['value'] = 0
        os.makedirs(folder, exist_ok=True)
        
        success = False
        
        try:
            if platform == 'TikTok':
                # Try multiple methods for TikTok
                status.config(text="Method 1: TikTok API...")
                success = self.download_tiktok_api(url, folder, status, progress)
                
                if not success:
                    progress['value'] = 0
                    status.config(text="Method 2: yt-dlp...")
                    success = self.download_tiktok_ytdlp(url, folder, status, progress)
                
                if not success:
                    # Try one more time with simplest options
                    progress['value'] = 0
                    status.config(text="Method 3: Simple download...")
                    opts = {
                        'format': 'worst',
                        'outtmpl': os.path.join(folder, 'tiktok_%(id)s.%(ext)s'),
                        'quiet': False,
                    }
                    try:
                        with yt_dlp.YoutubeDL(opts) as ydl:
                            ydl.download([url])
                        success = True
                    except:
                        pass
            
            else:
                # Instagram and Snapchat
                def hook(d):
                    if d['status'] == 'downloading':
                        try:
                            p = d.get('_percent_str', '0%').replace('%','')
                            progress['value'] = float(p)
                            status.config(text=f"Downloading {p}%")
                        except:
                            progress['value'] = 50
                    elif d['status'] == 'finished':
                        status.config(text="Processing...")
                        progress['value'] = 90
                
                opts = {
                    'format': 'best',
                    'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
                    'progress_hooks': [hook],
                    'quiet': True,
                    'no_warnings': True,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15'
                    }
                }
                
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                
                success = True
            
            if success:
                progress['value'] = 100
                status.config(text=f"✅ Downloaded from {platform}!")
                messagebox.showinfo("Success", f"Successfully downloaded from {platform}!\n\nSaved to: {folder}")
            else:
                raise Exception("All download methods failed")
            
        except Exception as e:
            status.config(text="❌ Download Failed")
            progress['value'] = 0
            
            error_msg = str(e)
            if platform == 'TikTok':
                messagebox.showerror("TikTok Error", 
                    "TikTok download failed.\n\n"
                    "Possible reasons:\n"
                    "• Video is private or deleted\n"
                    "• Regional restrictions\n"
                    "• TikTok changed their system\n\n"
                    "Try:\n"
                    "• Copy the link again\n"
                    "• Use a different TikTok video\n"
                    "• Check if video is public")
            elif platform == 'Snapchat':
                messagebox.showerror("Snapchat Error",
                    "Snapchat download failed.\n\n"
                    "Note: Snapchat stories and some content\n"
                    "require login or may be expired.\n\n"
                    "Public Spotlight videos work best!")
            else:
                messagebox.showerror("Error", f"Download failed:\n{error_msg}")
        finally:
            self.downloading = False

dl = Downloader()

def start():
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("Warning", "Please enter URL")
        return
    threading.Thread(target=lambda: dl.download(
        url, folder_var.get(), status_label, progress_bar, platform_label
    ), daemon=True).start()

def paste():
    url_entry.delete(0, tk.END)
    try:
        url_entry.insert(0, root.clipboard_get())
        p = dl.detect_platform(root.clipboard_get())
        if p != 'Unknown':
            platform_label.config(text=f"Platform: {p}")
    except:
        pass

def choose():
    path = filedialog.askdirectory()
    if path:
        folder_var.set(path)

# GUI
root = tk.Tk()
root.title(" Muscat Downloader 🇴🇲 ")
root.geometry("700x520")
root.resizable(False, False)
root.configure(bg="#0a0e14")

# Header
header = tk.Frame(root, bg="#16181d", height=110)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(header, text="🇴🇲 Muscat Downloader", 
         font=("Arial", 32, "bold"), bg="#16181d", fg="#00d9ff").pack(pady=12)
tk.Label(header, text="Snapchat • Instagram • TikTok", 
         font=("Arial", 13), bg="#16181d", fg="#888").pack()
tk.Label(header, text="Created by Mohammed Alfahdi", 
         font=("Arial", 11), bg="#16181d", fg="#555").pack(pady=4)

# Content
content = tk.Frame(root, bg="#0a0e14")
content.pack(fill="both", expand=True, padx=35, pady=25)

# Platform
platform_label = tk.Label(content, text="Platform: Not detected", 
                          font=("Arial", 13, "bold"), bg="#0a0e14", fg="#ff6b6b")
platform_label.pack(anchor="w", pady=(0, 15))

# URL
tk.Label(content, text="Video URL:", font=("Arial", 14, "bold"), 
         bg="#0a0e14", fg="#ddd").pack(anchor="w", pady=(0, 8))

url_fr = tk.Frame(content, bg="#0a0e14")
url_fr.pack(fill="x", pady=(0, 20))

url_entry = tk.Entry(url_fr, font=("Arial", 13), bg="#16181d", fg="#00d9ff",
                     relief="flat", insertbackground="#00d9ff", bd=0)
url_entry.pack(side="left", fill="x", expand=True, ipady=14, padx=(0, 12))

paste_btn = tk.Button(url_fr, text="📋 Paste", command=paste, 
                      bg="#e74c3c", fg="#000000", 
                      font=("Arial", 13, "bold"), relief="flat", cursor="hand2", 
                      padx=28, bd=0, activebackground="#c0392b", activeforeground="#000000")
paste_btn.pack(side="right")

# Folder
folder_fr = tk.Frame(content, bg="#0a0e14")
folder_fr.pack(fill="x", pady=(0, 30))

folder_var = tk.StringVar(value="downloads")
tk.Label(folder_fr, text="Save to: downloads", 
         font=("Arial", 12), bg="#0a0e14", fg="#888").pack(side="left")

folder_btn = tk.Button(folder_fr, text="📁 Change Folder", command=choose, 
                       bg="#9b59b6", fg="#000000",
                       font=("Arial", 11, "bold"), relief="flat", cursor="hand2", 
                       padx=18, pady=6, bd=0, activebackground="#8e44ad", activeforeground="#000000")
folder_btn.pack(side="right")

# Download Button
download_btn = tk.Button(content, text="⬇ DOWNLOAD NOW", command=start, 
                         bg="#27ae60", fg="#000000",
                         font=("Arial", 18, "bold"), relief="flat", cursor="hand2",
                         padx=50, pady=18, bd=0, activebackground="#229954", activeforeground="#000000")
download_btn.pack(pady=(15, 20))

# Progress Bar
style = ttk.Style()
style.configure("custom.Horizontal.TProgressbar", 
                background='#00d9ff', troughcolor='#16181d', 
                borderwidth=0, thickness=12)

progress_bar = ttk.Progressbar(content, length=630, mode='determinate',
                               style="custom.Horizontal.TProgressbar")
progress_bar.pack(pady=(0, 12))

# Status
status_label = tk.Label(content, text="Ready - Multiple download methods active", font=("Arial", 13), 
                        bg="#0a0e14", fg="#00d9ff")
status_label.pack()

# Info
tk.Label(content, text="✓ Snapchat: Spotlight & Public Stories (photos & videos) • Instagram • TikTok (3 methods)", 
         font=("Arial", 9), bg="#0a0e14", fg="#555").pack(pady=(15, 0))

root.mainloop()