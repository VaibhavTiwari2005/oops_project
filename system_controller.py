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

    def _try_launch(self, cmd_list):
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
        for k, v in self.APPS.items():
            if k in key:
                if isinstance(v, str):
                    webbrowser.open(v)
                    return f"Opening {k}"
                candidates = v.get(self.os_name, []) + v.get("Linux", []) if self.os_name != "Linux" else v.get("Linux", [])
                for cmd in candidates:
                    if self._try_launch(cmd):
                        return f"Opening {k}"
                return f"{k.capitalize()} not found on this system."
            
        if self._try_launch([key]):
            return f"Opening {key}"

        
        url = f"https://{key}.com"
        webbrowser.open(url)
        return f"Opening website {url}"
