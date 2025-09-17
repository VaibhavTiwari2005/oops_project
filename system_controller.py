import platform
import shutil
import subprocess
import webbrowser
import os
import sys
import time 
import wikipedia

# Windows-specific imports for volume and power control
if platform.system() == "Windows":
    try:
        import comtypes
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        import ctypes
    except ImportError:
        pass # Will be handled by methods that need it

# Linux-specific imports for power control
if platform.system() == "Linux":
    try:
        import dbus
    except ImportError:
        pass # Not critical for all functions

class SystemController:
    """
    Controls system-level functions like opening applications,
    managing volume, brightness, power settings, files, taking screenshots,
    sending emails, and controlling media playback.
    """
    APPS = {
        "notepad": {
            "Windows": ["notepad.exe"],
            "Darwin": ["open", "-a", "TextEdit"],
            "Linux": ["gedit", "xed", "nano"]
        },
        "calculator": {
            "Windows": ["calc.exe"],
            "Darwin": ["open", "-a", "Calculator"],
            "Linux": ["gnome-calculator", "kcalc", "xcalc"]
        },
        "task manager": {
            "Windows": ["taskmgr.exe"],
            "Darwin": ["open", "-a", "Activity Monitor"],
            "Linux": ["gnome-system-monitor", "htop"]
        },
        "terminal": {
            "Windows": ["cmd.exe"],
            "Darwin": ["open", "-a", "Terminal"],
            "Linux": ["gnome-terminal", "konsole"]
        },
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "email client": {
            "Windows": ["outlook.exe"],
            "Darwin": ["open", "-a", "Mail"],
            "Linux": ["thunderbird"]
        }
    }

    def __init__(self):
        self.os_name = platform.system()
        if self.os_name == "Windows":
            try:
                self.devices = AudioUtilities.GetSpeakers()
                self.interface = self.devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(self.interface, POINTER(IAudioEndpointVolume))
            except Exception as e:
                print(f"Warning: Could not initialize Windows audio control: {e}")
                self.volume = None

    def _try_launch(self, cmd_list):
        """Attempts to launch a process."""
        try:
            subprocess.Popen(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Error launching command {cmd_list}: {e}")
            return False

    def _get_volume_control_cmd(self, action, level=None):
        """Returns the appropriate command to control volume based on OS."""
        if self.os_name == "Linux":
            if action == "mute":
                return ["amixer", "-D", "pulse", "sset", "Master", "0%"]
            elif action == "unmute":
                return ["amixer", "-D", "pulse", "sset", "Master", "unmute"]
            elif action == "set":
                return ["amixer", "-D", "pulse", "sset", "Master", f"{level}%"]
            elif action == "increase":
                return ["amixer", "-D", "pulse", "sset", "Master", "5%+", "unmute"]
            elif action == "decrease":
                return ["amixer", "-D", "pulse", "sset", "Master", "5%-", "unmute"]
        elif self.os_name == "Darwin":
            if action == "mute":
                return ["osascript", "-e", "set volume output muted true"]
            elif action == "unmute":
                return ["osascript", "-e", "set volume output muted false"]
            elif action == "set":
                return ["osascript", "-e", f"set volume output volume {level}"]
            elif action == "increase":
                return ["osascript", "-e", "set volume output volume ((get volume settings)'s output volume + 5)"]
            elif action == "decrease":
                return ["osascript", "-e", "set volume output volume ((get volume settings)'s output volume - 5)"]
        return None

    def open_application(self, name: str) -> str:
        """
        Opens a system application or a website.
        If an application isn't found locally, it attempts to open it
        as a website.
        """
        key = name.lower()
        for k, v in self.APPS.items():
            if k in key:
                if isinstance(v, str):
                    webbrowser.open(v)
                    return f"Opening {k}"
                
                candidates = v.get(self.os_name, [])
                for cmd in candidates:
                    if self._try_launch(cmd):
                        return f"Opening {k}"
                return f"{k.capitalize()} not found on this system."

        if self._try_launch([key]):
            return f"Opening {key}"

        url = f"https://www.google.com/search?q=open+{key}"
        webbrowser.open(url)
        return f"Could not find {key} as an application. Opening web search for it."

    def open_file(self, file_path: str) -> str:
        """
        Opens a specific file or directory on the system.
        """
        file_path = os.path.expanduser(file_path)
        if not os.path.exists(file_path):
            return f"Error: File or directory '{file_path}' not found."

        try:
            if self.os_name == "Windows":
                os.startfile(file_path)
            elif self.os_name == "Darwin":
                subprocess.Popen(["open", file_path])
            else:
                subprocess.Popen(["xdg-open", file_path])
            return f"Opening {file_path}"
        except Exception as e:
            return f"Error opening file: {e}"

    def set_volume(self, level_or_action: [int, str]) -> str:
        """
        Sets the system volume to a specific percentage, or mutes/unmutes/increases/decreases.
        """
        if isinstance(level_or_action, int):
            level = level_or_action
            if not 0 <= level <= 100:
                return "Error: Volume level must be between 0 and 100."

            if self.os_name == "Windows":
                if not self.volume:
                    return "Windows audio control not initialized. Cannot set volume."
                try:
                    vol_range = self.volume.GetVolumeRange()
                    min_vol = vol_range[0]
                    max_vol = vol_range[1]
                    db_level = min_vol + (max_vol - min_vol) * (level / 100.0)
                    self.volume.SetMasterVolumeLevel(db_level, None)
                    return f"Setting volume to {level}%"
                except Exception as e:
                    return f"Error setting volume on Windows: {e}"
            else:
                cmd = self._get_volume_control_cmd("set", level)
                if cmd:
                    try:
                        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return f"Setting volume to {level}%"
                    except subprocess.CalledProcessError as e:
                        return f"Error setting volume: {e}"
                return "Volume control not supported on this OS."
        elif isinstance(level_or_action, str):
            action = level_or_action.lower()
            if action in ["mute", "unmute", "increase", "decrease"]:
                if self.os_name == "Windows":
                    if not self.volume:
                        return "Windows audio control not initialized. Cannot control volume."
                    try:
                        current_level = self.volume.GetMasterVolumeLevelScalar() * 100
                        if action == "mute":
                            self.volume.SetMute(1, None)
                            return "Muting volume."
                        elif action == "unmute":
                            self.volume.SetMute(0, None)
                            return "Unmuting volume."
                        elif action == "increase":
                            new_level = min(100, current_level + 5)
                            self.volume.SetMasterVolumeLevelScalar(new_level / 100.0, None)
                            return f"Increasing volume to {int(new_level)}%"
                        elif action == "decrease":
                            new_level = max(0, current_level - 5)
                            self.volume.SetMasterVolumeLevelScalar(new_level / 100.0, None)
                            return f"Decreasing volume to {int(new_level)}%"
                    except Exception as e:
                        return f"Error controlling volume on Windows: {e}"
                else:
                    cmd = self._get_volume_control_cmd(action)
                    if cmd:
                        try:
                            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            return f"{action.capitalize()}ing volume."
                        except subprocess.CalledProcessError as e:
                            return f"Error {action}ing volume: {e}"
                    return f"Volume {action} not supported on this OS."
            else:
                return "Invalid volume action. Use 'mute', 'unmute', 'increase', 'decrease' or a percentage."
        else:
            return "Invalid volume command type."

    def change_brightness(self, level: int) -> str:
        """
        Changes the screen brightness to a specific percentage.
        """
        if not 0 <= level <= 100:
            return "Error: Brightness level must be between 0 and 100."
        if self.os_name == "Windows":
            try:
                subprocess.run(["powershell.exe",
                                f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                return f"Setting brightness to {level}%"
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                return f"Error setting brightness on Windows. This method might require admin privileges or not be supported on your display."
        elif self.os_name == "Linux":
            try:
                output = subprocess.check_output(["xrandr", "--query"]).decode().split('\n')
                display_name = ""
                for line in output:
                    if " connected primary" in line:
                        display_name = line.split(" ")[0]
                        break
                if display_name:
                    brightness_val = level / 100.0
                    subprocess.run(["xrandr", "--output", display_name, "--brightness", f"{brightness_val}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return f"Setting brightness to {level}% on {display_name}"
                else:
                    return "Could not determine primary display for xrandr."
            except (FileNotFoundError, subprocess.CalledProcessError):
                return "Brightness control (xrandr) not found or failed."
        elif self.os_name == "Darwin":
            try:
                subprocess.run(["osascript", "-e", f"tell application \"System Events\" to set brightness of current display to {level / 100.0}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Setting brightness to {level}%"
            except (subprocess.CalledProcessError, FileNotFoundError):
                return "Brightness control not supported or failed on macOS."
        
        return "Brightness control not supported on this OS."
    
    def power_control(self, action: str) -> str:
        """
        Performs a power-related action (shutdown, restart, hibernate, lock).
        """
        action = action.lower()
        
        if action in ["shutdown", "restart"]:
            if self.os_name == "Windows":
                cmd = ["shutdown", "/s" if action == "shutdown" else "/r", "/t", "0"]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Initiating {action}."
            elif self.os_name == "Darwin":
                cmd = ["sudo", "shutdown", "-h", "now"] if action == "shutdown" else ["sudo", "reboot"]
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return f"Initiating {action}."
                except subprocess.CalledProcessError as e:
                    return f"Error: Command failed. You may need to run with sudo permissions. {e}"
            elif self.os_name == "Linux":
                cmd = ["sudo", "poweroff"] if action == "shutdown" else ["sudo", "reboot"]
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return f"Initiating {action}."
                except subprocess.CalledProcessError as e:
                    return f"Error: Command failed. You may need to run with sudo permissions. {e}"
            else:
                return f"{action.capitalize()} not supported on this OS."
        elif action == "hibernate" or action == "suspend":
            if self.os_name == "Windows":
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return "Initiating hibernation."
            elif self.os_name == "Linux":
                subprocess.run(["systemctl", "suspend"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return "Initiating suspend."
            return "Hibernation/Suspend not supported on this OS."
        elif action == "lock":
            if self.os_name == "Windows":
                ctypes.windll.user32.LockWorkStation()
                return "Locking the computer."
            elif self.os_name == "Darwin":
                subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return "Locking the computer."
            elif self.os_name == "Linux":
                try:
                    for locker_cmd in [["gnome-screensaver-command", "--lock"],
                                       ["xdg-screensaver", "lock"],
                                       ["dm-tool", "lock"]]:
                        if self._try_launch(locker_cmd):
                            return "Locking the screen."
                    return "Screen lock command not found. You may need to install a screensaver or locker."
                except Exception as e:
                    return f"Error locking screen on Linux: {e}"
            else:
                return "Screen lock not supported on this OS."
        
        return f"Unknown power control action: {action}"

    def get_system_status(self, query: str) -> str:
        """
        Provides information about the system state (e.g., battery level).
        Requires 'psutil' library.
        """
        query = query.lower()
        try:
            import psutil
            if "battery" in query:
                battery = psutil.sensors_battery()
                if battery:
                    return f"Battery is at {battery.percent}% and is {'plugged in' if battery.power_plugged else 'not plugged in'}."
                return "Battery status not available."
            elif "memory" in query or "ram" in query:
                memory = psutil.virtual_memory()
                return f"Total RAM: {memory.total / (1024**3):.2f} GB, Used: {memory.used / (1024**3):.2f} GB."
            elif "cpu" in query:
                cpu_percent = psutil.cpu_percent(interval=1)
                return f"CPU usage is at {cpu_percent}%."
            else:
                return "I can check battery, memory, or CPU status."
        except ImportError:
            return "I need the 'psutil' library to get system status. Please install it with 'pip install psutil'."
        except Exception as e:
            return f"Error getting system status: {e}"

    def manage_window(self, action: str) -> str:
        """
        Manages active windows (e.g., minimize, maximize, close).
        """
        action = action.lower()
        
        try:
            import pygetwindow as gw
            window = gw.getActiveWindow()
            if not window:
                return "No active window found."
            
            if action == "minimize":
                window.minimize()
                return "Minimizing the current window."
            elif action == "maximize":
                window.maximize()
                return "Maximizing the current window."
            elif action == "close":
                window.close()
                return "Closing the current window."
            else:
                return f"Unknown window action: {action}"

        except ImportError:
            return "I need the 'pygetwindow' library to manage windows. Please install it with 'pip install pygetwindow'."
        except Exception as e:
            return f"Error managing window: {e}"

    def take_screenshot(self, filepath: str = None) -> str:
        """
        Takes a screenshot of the entire screen and saves it.
        Requires 'Pillow' and 'mss' libraries.
        """
        try:
            from mss import mss
            from PIL import Image
            
            if filepath is None:
                filepath = os.path.join(os.path.expanduser("~"), "Pictures", f"screenshot_{int(time.time())}.png")
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with mss() as sct:
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                img.save(filepath)
            return f"Screenshot saved to: {filepath}"
        except ImportError:
            return "I need the 'mss' and 'Pillow' libraries to take screenshots. Please install them with 'pip install mss Pillow'."
        except Exception as e:
            return f"Error taking screenshot: {e}"

    def send_email(self, recipient: str, subject: str, body: str) -> str:
        """
        Opens the default email client with a pre-filled email.
        """
        try:
            mailto_link = f"mailto:{recipient}?subject={subject}&body={body}"
            webbrowser.open(mailto_link)
            return f"Opened email client for {recipient} with subject '{subject}'."
        except Exception as e:
            return f"Error opening email client: {e}"

    def media_control(self, action: str) -> str:
        """
        Controls media playback (play, pause, next, previous, stop).
        """
        action = action.lower()
        if self.os_name == "Windows":
            try:
                import ctypes
                key_map = {
                    "play": 0xB3, "pause": 0xB3, "play/pause": 0xB3,
                    "stop": 0xB2, "next": 0xB0, "previous": 0xB1
                }
                if action in key_map:
                    ctypes.windll.user32.keybd_event(key_map[action], 0, 0, 0)
                    time.sleep(0.1)
                    ctypes.windll.user32.keybd_event(key_map[action], 0, 2, 0)
                    return f"Performed media action: {action}"
                else:
                    return f"Unsupported media action on Windows: {action}"
            except Exception as e:
                return f"Error controlling media on Windows: {e}"
        elif self.os_name == "Linux":
            try:
                playerctl_cmd = ["playerctl", action]
                subprocess.run(playerctl_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Performed media action: {action}"
            except FileNotFoundError:
                return "I need 'playerctl' to control media on Linux. Please install it with 'sudo apt install playerctl'."
            except subprocess.CalledProcessError:
                return "No active media player found or action failed. Is a media player running?"
            except Exception as e:
                return f"Error controlling media on Linux: {e}"
        elif self.os_name == "Darwin":
            try:
                script_map = {
                    "play": "play", "pause": "pause", "play/pause": "playpause",
                    "stop": "stop", "next": "next track", "previous": "previous track"
                }
                if action in script_map:
                    subprocess.run(["osascript", "-e", f'tell application "Music" to {script_map[action]}'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return f"Performed media action: {action}"
                else:
                    return f"Unsupported media action on macOS: {action}"
            except subprocess.CalledProcessError:
                return "No active media player found (e.g., Music app) or action failed."
            except Exception as e:
                return f"Error controlling media on macOS: {e}"
        
        return "Media control not supported on this OS or requires additional setup."
    
# This is a new, standalone function for answering questions.
def answer_query_advanced(query: str) -> str:
    """
    Answers a general knowledge question using Wikipedia with advanced handling.
    This function provides more context and handles common issues to sound more impressive.

    Args:
        query: The question or search term from the user.

    Returns:
        A string containing the answer or a helpful error message.
    """
    try:
        search_results = wikipedia.search(query)
        
        if not search_results:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return f"Sorry, I couldn't find any Wikipedia pages for '{query}'. I'll open a web search for you."

        page_title = search_results[0]
        summary = wikipedia.summary(page_title, sentences=3)
        
        return f"According to Wikipedia, {summary}"

    except wikipedia.exceptions.PageError:
        return f"Sorry, the Wikipedia page for '{query}' could not be found."
    
    except wikipedia.exceptions.DisambiguationError as e:
        options = ', '.join(e.options[:4])
        return f"Your query '{query}' is ambiguous. Please be more specific. Did you mean: {options}?"
        
    except Exception as e:
        return f"An unexpected error occurred while looking for '{query}': {e}"