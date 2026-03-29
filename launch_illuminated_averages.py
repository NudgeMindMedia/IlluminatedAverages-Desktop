import ctypes
import subprocess
import sys
from pathlib import Path


def show_error(message):
    ctypes.windll.user32.MessageBoxW(0, message, "Illuminated Averages", 0x10)


def find_repo_root(start_dir):
    current = Path(start_dir).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "illuminated_average_tk.py").is_file():
            return candidate
        repo_candidate = candidate / "IlluminatedAverages_Repo"
        if (repo_candidate / "illuminated_average_tk.py").is_file():
            return repo_candidate
    raise FileNotFoundError("Could not find IlluminatedAverages_Repo next to this launcher.")


def main():
    launcher_dir = Path(sys.executable).resolve().parent

    try:
        repo_root = find_repo_root(launcher_dir)
        pythonw_path = repo_root.parent / ".venv" / "Scripts" / "pythonw.exe"
        app_script = repo_root / "illuminated_average_tk.py"

        if not pythonw_path.is_file():
            raise FileNotFoundError(f"Expected Python launcher was not found:\n{pythonw_path}")
        if not app_script.is_file():
            raise FileNotFoundError(f"Expected app script was not found:\n{app_script}")

        subprocess.Popen(
            [str(pythonw_path), str(app_script)],
            cwd=str(repo_root),
            close_fds=True,
        )
    except Exception as error:
        show_error(str(error))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
