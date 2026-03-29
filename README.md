# Illuminated Averages

Illuminated Averages is a Python app that reads a video, averages its frames over time, and saves the result as a single PNG image.

The project currently has two front ends:
- `illuminated_average.py` - command-line interface
- `illuminated_average_tk.py` - Tkinter desktop interface

Both front ends use the same core processing backend.

## Features

- local video file input
- YouTube URL input
- PNG output
- grayscale output option
- optional resizing and frame sampling
- repo-local download storage for YouTube source files

## Main Files

- `illuminated_average.py` - core processor and CLI entry point
- `illuminated_average_tk.py` - desktop UI
- `youtube_download.py` - YouTube download helper
- `downloads/` - local folder for downloaded YouTube videos

## Requirements

Python packages:
- `numpy`
- `Pillow`
- `yt-dlp`

External tools on `PATH`:
- `ffmpeg`
- `ffprobe`

## Recommended Python

Use the local virtual environment:

`C:\Users\User\Desktop\PythonEnvironment_Test\.venv`

## Command-Line Usage

### Local Video File

```powershell
& "c:\Users\User\Desktop\PythonEnvironment_Test\.venv\Scripts\python.exe" "c:\Users\User\Desktop\PythonEnvironment_Test\IlluminatedAverages_Repo\illuminated_average.py" "C:\path\to\video.mp4" "C:\path\to\output.png"
```

### YouTube URL

```powershell
& "c:\Users\User\Desktop\PythonEnvironment_Test\.venv\Scripts\python.exe" "c:\Users\User\Desktop\PythonEnvironment_Test\IlluminatedAverages_Repo\illuminated_average.py" --youtube-url "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir "C:\path\to\output_folder"
```

When using `--youtube-url`, the video is downloaded into `downloads/` and then processed like a local file.

## Useful Options

- `--fps 1` - sample one frame per second
- `--scale-width 640` - resize before averaging
- `--max-frames 500` - stop after a fixed number of frames
- `--grayscale` - save a grayscale image
- `--autocontrast` - stretch the output tonal range
- `--progress-every 50` - print progress every 50 frames

Example:

```powershell
& "c:\Users\User\Desktop\PythonEnvironment_Test\.venv\Scripts\python.exe" "c:\Users\User\Desktop\PythonEnvironment_Test\IlluminatedAverages_Repo\illuminated_average.py" --youtube-url "https://www.youtube.com/watch?v=VIDEO_ID" --output-dir "C:\Users\User\Desktop\FinishedImages" --fps 1 --scale-width 640 --autocontrast
```

## Desktop App

Launch the Tkinter UI with:

```powershell
& "c:\Users\User\Desktop\PythonEnvironment_Test\.venv\Scripts\python.exe" "c:\Users\User\Desktop\PythonEnvironment_Test\IlluminatedAverages_Repo\illuminated_average_tk.py"
```

The desktop app lets you:
- choose a local video file or enter a YouTube URL
- type or browse for the output image path
- generate the final illuminated average image from the window

## Notes

- `yt-dlp` runs through the active Python environment
- external `yt-dlp` config files are ignored
- downloaded source videos in `downloads/` are excluded by `.gitignore`
- recent smoke tests verified:
  - local CLI processing
  - grayscale output
  - YouTube helper validation
