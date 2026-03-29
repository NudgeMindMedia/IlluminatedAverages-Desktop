import re
import subprocess
import sys
from pathlib import Path


YOUTUBE_URL_PATTERN = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/).+",
    re.IGNORECASE,
)
MINIMUM_YT_DLP_VERSION = (2026, 2, 21)


def is_youtube_url(value):
    return bool(value and YOUTUBE_URL_PATTERN.match(value.strip()))


def parse_yt_dlp_version(version_text):
    match = re.match(r"^(\d{4})\.(\d{2})\.(\d{2})$", version_text.strip())
    if not match:
        raise RuntimeError(f"Could not parse yt-dlp version: {version_text!r}")
    return tuple(int(part) for part in match.groups())


def get_yt_dlp_command():
    return [sys.executable, "-m", "yt_dlp"]


def verify_youtube_downloader():
    command = get_yt_dlp_command() + ["--version"]
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "Unknown yt-dlp error."
        raise RuntimeError(
            "yt-dlp is not available in the current Python environment. "
            f"Details: {stderr}"
        )

    installed_version = parse_yt_dlp_version(result.stdout.strip())
    if installed_version < MINIMUM_YT_DLP_VERSION:
        minimum_version_text = ".".join(str(part).zfill(2) if index else str(part) for index, part in enumerate(MINIMUM_YT_DLP_VERSION))
        current_version_text = result.stdout.strip()
        raise RuntimeError(
            f"yt-dlp {current_version_text} is too old. Install yt-dlp {minimum_version_text} or newer."
        )


def ensure_download_directory(base_directory):
    download_directory = Path(base_directory) / "downloads"
    download_directory.mkdir(parents=True, exist_ok=True)
    return download_directory


def download_youtube_video(video_url, base_directory):
    verify_youtube_downloader()
    download_directory = ensure_download_directory(base_directory)

    # Let yt-dlp choose a safe filename while keeping the original extension.
    output_template = download_directory / "%(title).120s [%(id)s].%(ext)s"
    command = get_yt_dlp_command() + [
        "--ignore-config",
        "--no-playlist",
        "--restrict-filenames",
        "--format",
        "mp4/bestvideo*+bestaudio/best",
        "--merge-output-format",
        "mp4",
        "--output",
        str(output_template),
        "--print",
        "after_move:filepath",
        video_url,
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "Unknown yt-dlp error."
        raise RuntimeError(f"yt-dlp failed: {stderr}")

    downloaded_path = result.stdout.strip().splitlines()
    if not downloaded_path:
        raise RuntimeError("yt-dlp did not report a downloaded file path.")

    final_path = Path(downloaded_path[-1].strip())
    if not final_path.is_file():
        raise RuntimeError(f"Downloaded video file was not found: {final_path}")

    return final_path
