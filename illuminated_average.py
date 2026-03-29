import argparse
# Illuminated Averages v1.04
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from youtube_download import download_youtube_video, is_youtube_url


def verify_dependencies():
    # Fail early with a clear message if the external video tools are unavailable.
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            f"Required tool(s) not found on PATH: {joined}. Install FFmpeg and ensure ffmpeg/ffprobe are available."
        )


def probe_video_dimensions(input_video):
    # Ask ffprobe for the decoded video stream dimensions so frame reads are sized correctly.
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0:s=x",
        str(input_video),
    ]
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "Unknown ffprobe error."
        raise RuntimeError(f"ffprobe failed: {stderr}")

    output = result.stdout.strip()
    try:
        width_text, height_text = output.split("x", 1)
        width = int(width_text)
        height = int(height_text)
    except (ValueError, AttributeError):
        raise RuntimeError(f"Could not parse video dimensions from ffprobe output: {output!r}") from None

    if width <= 0 or height <= 0:
        raise RuntimeError(f"Invalid video dimensions reported by ffprobe: {width}x{height}")

    return width, height


def compute_scaled_dimensions(width, height, scale_width):
    # Preserve aspect ratio when the user requests a smaller working width.
    if scale_width is None:
        return width, height
    if scale_width <= 0:
        raise ValueError("--scale-width must be greater than zero.")

    scaled_height = max(1, int(round(height * (scale_width / width))))
    return int(scale_width), scaled_height


def build_ffmpeg_command(input_video, width, height, fps=None, grayscale=False):
    # Stream raw frames to stdout so Python can process them incrementally.
    command = ["ffmpeg", "-v", "error", "-i", str(input_video)]

    filters = []
    if fps is not None:
        if fps <= 0:
            raise ValueError("--fps must be greater than zero.")
        filters.append(f"fps={fps}")

    filters.append(f"scale={width}:{height}")

    if grayscale:
        filters.append("format=gray")
        pixel_format = "gray"
    else:
        filters.append("format=rgb24")
        pixel_format = "rgb24"

    command.extend(["-vf", ",".join(filters), "-f", "rawvideo", "-pix_fmt", pixel_format, "-"])
    return command


def autocontrast_array(image_array):
    # Stretch the averaged values to fill the full output range when requested.
    min_value = float(image_array.min())
    max_value = float(image_array.max())

    if max_value <= min_value:
        return np.zeros_like(image_array, dtype=np.uint8)

    stretched = (image_array - min_value) * (255.0 / (max_value - min_value))
    return np.clip(stretched, 0, 255).astype(np.uint8)


def stream_and_average_frames(
    input_video,
    source_width,
    source_height,
    fps=None,
    scale_width=None,
    max_frames=None,
    grayscale=False,
    progress_interval=100,
):
    width, height = compute_scaled_dimensions(source_width, source_height, scale_width)
    command = build_ffmpeg_command(input_video, width, height, fps=fps, grayscale=grayscale)

    channels = 1 if grayscale else 3
    frame_size = width * height * channels
    # Accumulate into float64 so long videos do not overflow the running sum.
    accumulator = np.zeros((height, width, channels), dtype=np.float64)
    frame_count = 0
    stopped_early = False

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        while True:
            if max_frames is not None and frame_count >= max_frames:
                stopped_early = True
                process.terminate()
                break

            chunk = process.stdout.read(frame_size)
            if not chunk:
                break
            if len(chunk) != frame_size:
                raise RuntimeError(
                    f"Incomplete frame received from ffmpeg: expected {frame_size} bytes, got {len(chunk)}."
                )

            # Read exactly one raw frame, reshape it, and add it into the running total.
            frame = np.frombuffer(chunk, dtype=np.uint8).reshape((height, width, channels))
            accumulator += frame
            frame_count += 1

            if progress_interval > 0 and frame_count % progress_interval == 0:
                print(f"Processed {frame_count} frames...", file=sys.stderr)

        stderr_output = process.stderr.read().decode("utf-8", errors="replace").strip()
        return_code = process.wait()
    finally:
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()

    if return_code not in (0, -15):
        if stopped_early:
            return_code = 0
        else:
            raise RuntimeError(f"ffmpeg failed: {stderr_output or 'Unknown ffmpeg error.'}")

    if frame_count == 0:
        raise RuntimeError("No frames were decoded. Check the input file and sampling options.")

    # Convert the running sum into a per-pixel temporal average.
    average = accumulator / frame_count
    if grayscale:
        average = average.reshape((height, width))

    return average, frame_count


def save_output(image_array, output_image, grayscale=False, autocontrast=False):
    if autocontrast:
        output_array = autocontrast_array(image_array)
    else:
        output_array = np.clip(np.rint(image_array), 0, 255).astype(np.uint8)

    # Pillow handles the final PNG encoding once the averaged pixel array is ready.
    mode = "L" if grayscale else "RGB"
    image = Image.fromarray(output_array, mode=mode)
    image.save(output_image, format="PNG")


def process_video_to_image(
    input_video,
    output_image,
    fps=None,
    scale_width=None,
    max_frames=None,
    grayscale=False,
    autocontrast=False,
    progress_every=100,
):
    input_video = Path(input_video)
    output_image = Path(output_image)

    if not input_video.is_file():
        raise ValueError(f"Input video does not exist: {input_video}")
    if max_frames is not None and max_frames <= 0:
        raise ValueError("--max-frames must be greater than zero.")
    if progress_every is not None and progress_every < 0:
        raise ValueError("--progress-every cannot be negative.")

    verify_dependencies()
    source_width, source_height = probe_video_dimensions(input_video)
    averaged_image, frame_count = stream_and_average_frames(
        input_video=input_video,
        source_width=source_width,
        source_height=source_height,
        fps=fps,
        scale_width=scale_width,
        max_frames=max_frames,
        grayscale=grayscale,
        progress_interval=progress_every,
    )
    output_image.parent.mkdir(parents=True, exist_ok=True)
    save_output(
        image_array=averaged_image,
        output_image=output_image,
        grayscale=grayscale,
        autocontrast=autocontrast,
    )
    return output_image, frame_count


def build_output_path(input_video, output_image=None, output_dir=None):
    if output_image and output_dir:
        raise ValueError("Provide either output_image or --output-dir, not both.")
    if output_dir is not None:
        output_directory = Path(output_dir)
        return output_directory / f"{Path(input_video).stem}_illuminated_average.png"
    if output_image is not None:
        return Path(output_image)
    raise ValueError("Provide an output image path or use --output-dir.")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Average video frames over time into a single illuminated composite image."
    )
    parser.add_argument("input_video", nargs="?", help="Path to the input video file.")
    parser.add_argument("output_image", nargs="?", help="Path to the output PNG image.")
    parser.add_argument(
        "--youtube-url",
        help="YouTube video URL to download into the repo downloads folder before averaging.",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory where the output PNG should be saved. The filename is generated automatically.",
    )
    parser.add_argument("--fps", type=float, help="Sample frames at a fixed FPS before averaging.")
    parser.add_argument(
        "--scale-width",
        type=int,
        help="Resize video to this width before averaging. Aspect ratio is preserved.",
    )
    parser.add_argument("--max-frames", type=int, help="Stop after this many decoded frames.")
    parser.add_argument("--grayscale", action="store_true", help="Average luminance and save a grayscale PNG.")
    parser.add_argument(
        "--autocontrast",
        action="store_true",
        help="Stretch the averaged image tonal range to the full 0-255 output range.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=100,
        help="Print progress every N frames. Use 0 to disable progress output.",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.youtube_url and args.input_video:
        parser.error("Provide either input_video or --youtube-url, not both.")
    if not args.youtube_url and not args.input_video:
        parser.error("Provide an input video path or use --youtube-url.")
    if args.output_image and args.output_dir:
        parser.error("Provide either output_image or --output-dir, not both.")
    if not args.output_image and not args.output_dir:
        parser.error("Provide an output image path or use --output-dir.")

    repo_root = Path(__file__).resolve().parent
    if args.youtube_url:
        if not is_youtube_url(args.youtube_url):
            parser.error("The value provided to --youtube-url does not look like a valid YouTube link.")
        input_video = download_youtube_video(args.youtube_url, repo_root)
    else:
        input_video = Path(args.input_video)

    if not input_video.is_file():
        parser.error(f"Input video does not exist: {input_video}")
    if args.max_frames is not None and args.max_frames <= 0:
        parser.error("--max-frames must be greater than zero.")
    if args.progress_every is not None and args.progress_every < 0:
        parser.error("--progress-every cannot be negative.")

    try:
        output_image = build_output_path(
            input_video=input_video,
            output_image=args.output_image,
            output_dir=args.output_dir,
        )
        output_image, frame_count = process_video_to_image(
            input_video=input_video,
            output_image=output_image,
            fps=args.fps,
            scale_width=args.scale_width,
            max_frames=args.max_frames,
            grayscale=args.grayscale,
            autocontrast=args.autocontrast,
            progress_every=args.progress_every,
        )
    except (RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Saved averaged image to {output_image} from {frame_count} frame(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
