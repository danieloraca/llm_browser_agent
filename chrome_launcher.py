import os
import platform
import subprocess
import time
import socket
import sys
import psutil
from pathlib import Path

def is_port_in_use(port):
    """Check if the specified port is already in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result == 0
    except:
        return False

def get_chrome_process():
    """Get the Chrome process if it's running."""
    chrome_names = ['chrome', 'google chrome', 'google-chrome', 'chromium']
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'].lower()
            if any(name in proc_name for name in chrome_names):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

def get_default_chrome_profile():
    """Get the path to the user's default Chrome profile directory."""
    system = platform.system()
    home = Path.home()
    
    if system == "Darwin":  # macOS
        return home / "Library/Application Support/Google/Chrome"
    elif system == "Windows":
        local_app_data = os.environ.get('LOCALAPPDATA', '')
        if local_app_data:
            return Path(local_app_data) / "Google/Chrome/User Data"
        return None
    elif system == "Linux":
        return home / ".config/google-chrome"
    else:
        return None

def launch_chrome_with_debugging(port=9222, use_default_profile=True, mode=None):
    """
    Launch Chrome with remote debugging enabled, with options for handling existing Chrome sessions.
    
    Args:
        port: The debugging port to use
        use_default_profile: Whether to try using default profile with login details
        mode: How to handle existing Chrome sessions:
              - "close_reopen": Close Chrome and reopen with debug + default profile (has logins)
              - "new_window": Open a new Chrome window without closing existing (no logins)
              - None: Prompt the user to choose (interactive mode)
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if debugging port is already in use
    if is_port_in_use(port):
        print(f"✅ Chrome already running with remote debugging on port {port}")
        return True
    
    # Check if Chrome is already running (without debugging)
    chrome_proc = get_chrome_process()
    chrome_running = chrome_proc is not None
    
    # Get default profile information
    profile_dir = get_default_chrome_profile()
    if profile_dir and profile_dir.exists():
        print(f"Found default Chrome profile at: {profile_dir}")
        default_profile_found = True
    else:
        print("⚠️ Default Chrome profile not found")
        app_dir = os.path.dirname(os.path.abspath(__file__))
        profile_dir = Path(app_dir) / "chrome_profile"
        print(f"Falling back to local profile at: {profile_dir}")
        default_profile_found = False
    
    # If Chrome is already running, handle according to mode
    if chrome_running:
        print(f"⚠️ Chrome is already running but not in debug mode")
        
        # If no mode specified, ask user
        if mode is None:
            print("Choose an option:")
            print("1. Close current Chrome and reopen with debugging (keeps login information)")
            print("2. Open a new Chrome window with debugging (without login information)")
            choice = input("Enter 1 or 2: ").strip()
            
            if choice == "1":
                mode = "close_reopen"
            else:
                mode = "new_window"
        
        if mode == "close_reopen":
            print("Closing Chrome and reopening with debugging enabled...")
            close_chrome()
            time.sleep(3)  # Wait for Chrome to fully close
            
            # Check if Chrome really closed
            if get_chrome_process():
                print("⚠️ Chrome is still running. Trying more aggressive close...")
                system = platform.system()
                if system == "Darwin":  # macOS
                    subprocess.run(["killall", "-9", "Google Chrome"], check=False)
                elif system == "Windows":
                    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], check=False)
                elif system == "Linux":
                    subprocess.run(["killall", "-9", "chrome", "chromium"], check=False)
                time.sleep(2)
            
            # Now Chrome is closed, so we'll treat this like Chrome wasn't running
            chrome_running = False
            print("✅ Chrome closed successfully")
        
        elif mode == "new_window":
            print("Opening a new Chrome window with debugging (without login information)...")
            # Continue with temp profile approach, handled below
    
    # Set up the system-specific Chrome launch command
    system = platform.system()
    chrome_process = None
    
    try:
        # Launch Chrome with the appropriate profile based on situation
        if system == "Darwin":  # macOS
            if chrome_running:  # Using new_window mode
                # Create a temporary profile for the new window
                temp_profile_dir = Path(os.path.expanduser("~/Library/Application Support/Google/ChromeTemp"))
                os.makedirs(temp_profile_dir, exist_ok=True)
                
                cmd = [
                    "open", "-n", "-a", "Google Chrome", 
                    "--args", f"--remote-debugging-port={port}",
                    "--no-first-run", "--no-default-browser-check",
                    f"--user-data-dir={temp_profile_dir}"
                ]
                print("ℹ️ Using temporary profile without login information")
            else:
                # Chrome is not running or we closed it
                cmd = [
                    "open", "-a", "Google Chrome", 
                    "--args", f"--remote-debugging-port={port}",
                    "--no-first-run", "--no-default-browser-check"
                ]
                
                # Only add user-data-dir if NOT using default profile
                if not use_default_profile or not default_profile_found:
                    cmd.append(f"--user-data-dir={profile_dir}")
                    print("ℹ️ Using custom profile")
                else:
                    print("✓ Using default profile with your login information")
            
            print(f"Executing: {' '.join(cmd)}")
            chrome_process = subprocess.Popen(cmd)
            print(f"🚀 Launched Chrome on macOS with debugging port {port}")
            
        elif system == "Windows":
            # Find Chrome executable
            chrome_paths = [
                os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Google\\Chrome\\Application\\chrome.exe'),
                os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Google\\Chrome\\Application\\chrome.exe'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google\\Chrome\\Application\\chrome.exe')
            ]
            
            chrome_path = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_path = path
                    break
            
            # Build command with profile if needed
            if chrome_path:
                if chrome_running:  # Using new_window mode
                    # Use a temporary profile when Chrome is already running
                    temp_profile_dir = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'ChromeTemp')
                    os.makedirs(temp_profile_dir, exist_ok=True)
                    
                    cmd = [
                        chrome_path, 
                        f"--remote-debugging-port={port}",
                        "--no-first-run",
                        "--no-default-browser-check",
                        f"--user-data-dir={temp_profile_dir}"
                    ]
                    print("ℹ️ Using temporary profile without login information")
                else:
                    # Chrome not running or we closed it
                    cmd = [
                        chrome_path, 
                        f"--remote-debugging-port={port}",
                        "--no-first-run",
                        "--no-default-browser-check"
                    ]
                    
                    # Only add user-data-dir if NOT using default profile
                    if not use_default_profile or not default_profile_found:
                        cmd.append(f"--user-data-dir={profile_dir}")
                        print("ℹ️ Using custom profile")
                    else:
                        print("✓ Using default profile with your login information")
                
                print(f"Executing: {' '.join(cmd)}")
                chrome_process = subprocess.Popen(cmd)
                print(f"🚀 Launched Chrome on Windows with debugging port {port}")
            else:
                # Fallback with shell=True when chrome path not found
                if chrome_running:  # Using new_window mode
                    temp_profile_dir = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'ChromeTemp')
                    os.makedirs(temp_profile_dir, exist_ok=True)
                    cmd = f"start chrome --remote-debugging-port={port} --no-first-run --user-data-dir=\"{temp_profile_dir}\""
                    print("ℹ️ Using temporary profile without login information")
                else:
                    # Chrome not running or we closed it
                    cmd = f"start chrome --remote-debugging-port={port} --no-first-run"
                    if not use_default_profile or not default_profile_found:
                        cmd += f" --user-data-dir=\"{profile_dir}\""
                        print("ℹ️ Using custom profile")
                    else:
                        print("✓ Using default profile with your login information")
                
                print(f"Executing: {cmd}")
                subprocess.Popen(cmd, shell=True)
                print(f"🚀 Attempted to launch Chrome using 'start chrome' command")
                
        elif system == "Linux":
            # Try different browser commands common on Linux
            for browser_cmd in ["google-chrome", "chrome", "chromium", "chromium-browser"]:
                try:
                    if chrome_running:  # Using new_window mode
                        # When Chrome is already running, use a temporary profile
                        temp_profile_dir = "/tmp/chromeTemp"
                        os.makedirs(temp_profile_dir, exist_ok=True)
                        
                        cmd = [
                            browser_cmd, 
                            f"--remote-debugging-port={port}",
                            "--no-first-run",
                            "--no-default-browser-check",
                            f"--user-data-dir={temp_profile_dir}"
                        ]
                        print("ℹ️ Using temporary profile without login information")
                    else:
                        # Chrome not running or we closed it
                        cmd = [
                            browser_cmd, 
                            f"--remote-debugging-port={port}",
                            "--no-first-run",
                            "--no-default-browser-check"
                        ]
                        
                        # Only add user-data-dir if NOT using default profile
                        if not use_default_profile or not default_profile_found:
                            cmd.append(f"--user-data-dir={profile_dir}")
                            print("ℹ️ Using custom profile")
                        else:
                            print("✓ Using default profile with your login information")
                            
                    print(f"Executing: {' '.join(cmd)}")
                    chrome_process = subprocess.Popen(cmd)
                    print(f"🚀 Launched {browser_cmd} on Linux with debugging port {port}")
                    break
                except FileNotFoundError:
                    continue
            else:
                print("❌ Could not find Chrome/Chromium browser on Linux")
                return False
        else:
            print(f"❌ Unsupported operating system: {system}")
            return False
            
        # Wait for Chrome to start and open the debugging port
        print("Giving Chrome extra time to start...")
        time.sleep(5)  # Initial delay
        
        max_attempts = 20
        for attempt in range(max_attempts):
            # Check if the port is open
            if is_port_in_use(port):
                print(f"✅ Verified Chrome is running with debugging port {port}")
                return True
                
            # Try HTTP request to check debugging endpoint
            try:
                import urllib.request
                with urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=1) as response:
                    if response.status == 200:
                        print(f"✅ Verified Chrome debugging endpoint is responding on port {port}")
                        return True
            except:
                pass
                
            print(f"Waiting for Chrome to start (attempt {attempt+1}/{max_attempts})...")
            time.sleep(2)
            
        print("⚠️ Chrome started but debugging port is not responding")
        print("Continuing anyway... the browser might work regardless")
        return True
        
    except Exception as e:
        print(f"❌ Error launching Chrome: {str(e)}")
        return False

def close_chrome():
    """Close Chrome browser."""
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            os.system("pkill -f 'Google Chrome'")
        elif system == "Windows":
            os.system("taskkill /F /IM chrome.exe")
        elif system == "Linux":
            os.system("pkill -f 'chrome|chromium'")
        else:
            print(f"❌ Unsupported operating system: {system}")
            return False
        return True
    except Exception as e:
        print(f"❌ Error closing Chrome: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the launcher when run directly
    launch_chrome_with_debugging(use_default_profile=True)