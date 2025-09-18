import platform
import shutil
import subprocess
import webbrowser

class SystemController:
    
    APPS = {
        "notepad": {
            "Windows": [["notepad"]],
            "Darwin": [["open", "-a", "TextEdit"]],
            "Linux": [["gedit"], ["xed"], ["nano"]]
        },
        "calculator": {
            "Windows": [["calc"]],
            "Darwin": [["open", "-a", "Calculator"]],
            "Linux": [["gnome-calculator"], ["kcalc"], ["xcalc"]]
        },
        "youtube": "https://youtube.com",
        "google": "https://google.com"
    }

    def __init__(self):
        self.os_name = platform.system()

    def _try_launch(self, cmd_list: list) -> bool:
        exe = cmd_list[0]
        
        if shutil.which(exe) is None and not (self.os_name == "Windows" and exe.lower() in ("start", "cmd")):
            return False

        try:
            subprocess.Popen(cmd_list)
            return True
        except Exception:
            return False

    def open_application(self, name: str) -> str:
        key = name.lower()

        for app_name, v in self.APPS.items():
            if app_name in key or key in app_name: 
                
                if isinstance(v, str):
                    webbrowser.open(v)
                    return f"Opening website: {app_name}"

                candidates = v.get(self.os_name, [])
                if self.os_name != "Linux":
                    candidates += v.get("Linux", [])
                
                for cmd in candidates:
                    if self._try_launch(cmd):
                        return f"Opening application: {app_name}"

                return f"{app_name.capitalize()} not found on this system using defined commands."

        if self._try_launch([key]):
            return f"Opening application: {key}"

        url = f"https://{key}.com"
        webbrowser.open(url)
        return f"Opening website fallback: {url}"