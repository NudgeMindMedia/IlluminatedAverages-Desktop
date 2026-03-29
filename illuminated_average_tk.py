import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from illuminated_average import build_output_path, process_video_to_image
from youtube_download import download_youtube_video, is_youtube_url


class IlluminatedAverageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Illuminated Averages")
        self.root.geometry("760x420")

        self.repo_root = Path(__file__).resolve().parent

        self.input_mode = tk.StringVar(value="local")
        self.local_video_path = tk.StringVar()
        self.youtube_url = tk.StringVar()
        self.output_image_path = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready.")

        self._build_ui()
        self._refresh_input_mode()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        ttk.Label(main, text="Input Source").grid(row=0, column=0, sticky="w", pady=(0, 8))

        mode_frame = ttk.Frame(main)
        mode_frame.grid(row=0, column=1, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Radiobutton(
            mode_frame,
            text="Local Video File",
            variable=self.input_mode,
            value="local",
            command=self._refresh_input_mode,
        ).grid(row=0, column=0, padx=(0, 16))
        ttk.Radiobutton(
            mode_frame,
            text="YouTube URL",
            variable=self.input_mode,
            value="youtube",
            command=self._refresh_input_mode,
        ).grid(row=0, column=1)

        self.local_label = ttk.Label(main, text="Local Video Path")
        self.local_label.grid(row=1, column=0, sticky="w", pady=6)
        self.local_entry = ttk.Entry(main, textvariable=self.local_video_path)
        self.local_entry.grid(row=1, column=1, sticky="ew", pady=6)
        self.local_button = ttk.Button(main, text="Browse...", command=self._choose_local_video)
        self.local_button.grid(row=1, column=2, sticky="ew", padx=(8, 0), pady=6)

        self.youtube_label = ttk.Label(main, text="YouTube URL")
        self.youtube_label.grid(row=2, column=0, sticky="w", pady=6)
        self.youtube_entry = ttk.Entry(main, textvariable=self.youtube_url)
        self.youtube_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=6)

        ttk.Label(main, text="Output Image Path").grid(row=3, column=0, sticky="w", pady=6)
        self.output_entry = ttk.Entry(main, textvariable=self.output_image_path)
        self.output_entry.grid(row=3, column=1, sticky="ew", pady=6)
        ttk.Button(main, text="Browse...", command=self._choose_output_path).grid(
            row=3, column=2, sticky="ew", padx=(8, 0), pady=6
        )

        hint = (
            "Enter a full output image path such as "
            "C:\\Images\\result.png, or browse to choose one."
        )
        ttk.Label(main, text=hint, foreground="#555555", wraplength=620).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(0, 14)
        )

        self.run_button = ttk.Button(main, text="Create Illuminated Average", command=self._start_processing)
        self.run_button.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 14))

        ttk.Label(main, text="Status").grid(row=6, column=0, sticky="nw")
        self.status_label = ttk.Label(main, textvariable=self.status_text, wraplength=620, justify="left")
        self.status_label.grid(row=6, column=1, columnspan=2, sticky="w")

    def _refresh_input_mode(self):
        local_mode = self.input_mode.get() == "local"

        if local_mode:
            self.local_entry.configure(state="normal")
            self.local_button.configure(state="normal")
            self.youtube_entry.configure(state="disabled")
        else:
            self.local_entry.configure(state="disabled")
            self.local_button.configure(state="disabled")
            self.youtube_entry.configure(state="normal")

    def _choose_local_video(self):
        file_path = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=[
                ("Video files", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            self.local_video_path.set(file_path)

    def _choose_output_path(self):
        file_path = filedialog.asksaveasfilename(
            title="Choose output image path",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("All files", "*.*")],
        )
        if file_path:
            self.output_image_path.set(file_path)

    def _start_processing(self):
        try:
            input_video, output_image = self._validate_inputs()
        except ValueError as error:
            messagebox.showerror("Invalid Input", str(error))
            return

        self.run_button.configure(state="disabled")
        self.status_text.set("Processing started. This can take a while for longer videos.")

        worker = threading.Thread(
            target=self._run_processing_job,
            args=(input_video, output_image),
            daemon=True,
        )
        worker.start()

    def _validate_inputs(self):
        output_path_text = self.output_image_path.get().strip()
        if not output_path_text:
            raise ValueError("Please enter or browse for an output image path.")

        output_image = Path(output_path_text)
        if output_image.suffix.lower() != ".png":
            output_image = output_image.with_suffix(".png")

        if self.input_mode.get() == "local":
            local_path_text = self.local_video_path.get().strip()
            if not local_path_text:
                raise ValueError("Please enter or browse for a local video file path.")
            input_video = Path(local_path_text)
            if not input_video.is_file():
                raise ValueError(f"Local video file was not found: {input_video}")
            return input_video, output_image

        youtube_url = self.youtube_url.get().strip()
        if not youtube_url:
            raise ValueError("Please enter a YouTube URL.")
        if not is_youtube_url(youtube_url):
            raise ValueError("Please enter a valid YouTube URL.")
        return youtube_url, output_image

    def _run_processing_job(self, input_value, output_image):
        try:
            if self.input_mode.get() == "youtube":
                self._set_status("Downloading YouTube video...")
                input_video = download_youtube_video(input_value, self.repo_root)
            else:
                input_video = input_value

            self._set_status("Averaging video frames into a single image...")
            output_image, frame_count = process_video_to_image(
                input_video=input_video,
                output_image=output_image,
            )
        except (RuntimeError, ValueError) as error:
            self.root.after(0, self._handle_error, str(error))
            return

        success_message = f"Saved image to {output_image} from {frame_count} frame(s)."
        self.root.after(0, self._handle_success, success_message)

    def _set_status(self, message):
        self.root.after(0, lambda: self.status_text.set(message))

    def _handle_error(self, message):
        self.run_button.configure(state="normal")
        self.status_text.set(f"Error: {message}")
        messagebox.showerror("Processing Failed", message)

    def _handle_success(self, message):
        self.run_button.configure(state="normal")
        self.status_text.set(message)
        messagebox.showinfo("Processing Complete", message)


def main():
    root = tk.Tk()
    app = IlluminatedAverageApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
