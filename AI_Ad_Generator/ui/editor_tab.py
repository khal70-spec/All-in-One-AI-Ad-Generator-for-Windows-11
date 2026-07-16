import customtkinter as ctk
from ui.styles import COLORS, FONTS
from core.video_editor import VideoEditor
from tkinter import filedialog
import threading
import os


class EditorTab:
    """Video editing tab"""

    def __init__(self, parent):
        self.parent = parent
        self.editor = VideoEditor()
        self.selected_video = None
        self.video_list = []

        self._create_ui()

    def _create_ui(self):
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ============ LEFT PANEL ============
        left_panel = ctk.CTkScrollableFrame(main_frame, width=400,
                                          fg_color=COLORS["bg_medium"],
                                          corner_radius=10)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        ctk.CTkLabel(left_panel, text="✂️ Video Editor",
                     font=FONTS["heading"]).pack(pady=(10, 15))

        # Select Video
        ctk.CTkButton(
            left_panel,
            text="📁 Select Video",
            height=40,
            fg_color=COLORS["bg_light"],
            hover_color=COLORS["accent"],
            command=self._select_video,
        ).pack(fill="x", padx=10, pady=5)

        self.video_path_label = ctk.CTkLabel(
            left_panel, text="No video selected",
            font=FONTS["small"], text_color=COLORS["text_secondary"],
        )
        self.video_path_label.pack(padx=10, pady=2)

        # ---- ADD TEXT ----
        ctk.CTkLabel(left_panel, text="📝 Add Text Overlay",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(20, 5))

        self.text_entry = ctk.CTkEntry(
            left_panel,
            placeholder_text="Enter text for overlay...",
            fg_color=COLORS["entry_bg"],
        )
        self.text_entry.pack(fill="x", padx=10, pady=5)

        self.text_pos_var = ctk.StringVar(value="bottom")
        ctk.CTkOptionMenu(
            left_panel,
            variable=self.text_pos_var,
            values=["top", "center", "bottom"],
            fg_color=COLORS["entry_bg"],
            button_color=COLORS["accent"],
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            left_panel,
            text="Add Text",
            fg_color=COLORS["accent"],
            command=self._add_text,
        ).pack(fill="x", padx=10, pady=5)

        # ---- ADD MUSIC ----
        ctk.CTkLabel(left_panel, text="🎵 Add Music",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(20, 5))

        ctk.CTkButton(
            left_panel,
            text="Select Audio File",
            fg_color=COLORS["bg_light"],
            command=self._select_audio,
        ).pack(fill="x", padx=10, pady=5)

        self.audio_path_label = ctk.CTkLabel(
            left_panel, text="No audio selected",
            font=FONTS["small"], text_color=COLORS["text_secondary"],
        )
        self.audio_path_label.pack(padx=10, pady=2)

        ctk.CTkLabel(left_panel, text="Volume:", font=FONTS["body"]).pack(
            anchor="w", padx=10, pady=(5, 0))
        self.volume_slider = ctk.CTkSlider(left_panel, from_=0, to=1, number_of_steps=100)
        self.volume_slider.set(0.5)
        self.volume_slider.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            left_panel,
            text="Add Music",
            fg_color=COLORS["accent"],
            command=self._add_music,
        ).pack(fill="x", padx=10, pady=5)

        # ---- COMBINE VIDEOS ----
        ctk.CTkLabel(left_panel, text="🔗 Combine Videos",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(20, 5))

        ctk.CTkButton(
            left_panel,
            text="Add Videos to List",
            fg_color=COLORS["bg_light"],
            command=self._add_to_list,
        ).pack(fill="x", padx=10, pady=5)

        self.list_label = ctk.CTkLabel(
            left_panel, text="Videos: 0",
            font=FONTS["small"], text_color=COLORS["text_secondary"],
        )
        self.list_label.pack(padx=10, pady=2)

        ctk.CTkButton(
            left_panel,
            text="Combine All",
            fg_color=COLORS["accent"],
            command=self._combine_videos,
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            left_panel,
            text="Clear List",
            fg_color=COLORS["error"],
            command=self._clear_list,
        ).pack(fill="x", padx=10, pady=5)

        # ---- LOOP VIDEO ----
        ctk.CTkLabel(left_panel, text="🔄 Loop Video",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(20, 5))

        loop_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        loop_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(loop_frame, text="Loops:", font=FONTS["body"]).pack(side="left")
        self.loop_entry = ctk.CTkEntry(loop_frame, width=60, fg_color=COLORS["entry_bg"])
        self.loop_entry.pack(side="left", padx=10)
        self.loop_entry.insert(0, "3")

        ctk.CTkButton(
            loop_frame,
            text="Loop",
            width=80,
            fg_color=COLORS["accent"],
            command=self._loop_video,
        ).pack(side="left", padx=5)

        # ---- SPEED ----
        ctk.CTkLabel(left_panel, text="⏩ Adjust Speed",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(20, 5))

        speed_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        speed_frame.pack(fill="x", padx=10, pady=5)

        for speed, label in [(0.5, "0.5x"), (1.0, "1x"), (1.5, "1.5x"), (2.0, "2x")]:
            ctk.CTkButton(
                speed_frame,
                text=label,
                width=60,
                fg_color=COLORS["bg_light"],
                command=lambda s=speed: self._change_speed(s),
            ).pack(side="left", padx=2)

        # Progress
        self.progress_label = ctk.CTkLabel(
            left_panel, text="Ready",
            font=FONTS["small"], text_color=COLORS["text_secondary"],
        )
        self.progress_label.pack(padx=10, pady=15)

        # ============ RIGHT PANEL ============
        right_panel = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_medium"],
                                  corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(right_panel, text="📺 Preview",
                     font=FONTS["heading"]).pack(pady=10)

        preview = ctk.CTkFrame(right_panel, fg_color=COLORS["bg_dark"],
                              corner_radius=10)
        preview.pack(expand=True, fill="both", padx=20, pady=10)

        ctk.CTkLabel(preview, text="Video preview\n\n🎬",
                     font=FONTS["body"],
                     text_color=COLORS["text_secondary"]).pack(expand=True)

        btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="📂 Open Output",
                      fg_color=COLORS["bg_light"],
                      command=lambda: os.startfile("outputs")).pack(side="left", padx=5)

    def _select_video(self):
        path = filedialog.askopenfilename(
            filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv"), ("All", "*.*")])
        if path:
            self.selected_video = path
            self.video_path_label.configure(text=os.path.basename(path))

    def _select_audio(self):
        path = filedialog.askopenfilename(
            filetypes=[("Audio", "*.mp3 *.wav *.ogg *.m4a"), ("All", "*.*")])
        if path:
            self.selected_audio = path
            self.audio_path_label.configure(text=os.path.basename(path))

    def _add_text(self):
        if not self.selected_video:
            self.progress_label.configure(text="⚠️ Select a video first!")
            return

        text = self.text_entry.get()
        if not text:
            return

        self.progress_label.configure(text="Adding text...")

        def run():
            try:
                output = self.editor.add_text_to_video(
                    self.selected_video, text, self.text_pos_var.get())
                self.parent.after(0, lambda: self.progress_label.configure(
                    text=f"✅ Saved: {os.path.basename(output)}"))
            except Exception as e:
                self.parent.after(0, lambda: self.progress_label.configure(
                    text=f"❌ Error: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def _add_music(self):
        if not self.selected_video or not hasattr(self, 'selected_audio'):
            self.progress_label.configure(text="⚠️ Select video and audio!")
            return

        self.progress_label.configure(text="Adding music...")

        def run():
            try:
                output = self.editor.add_music(
                    self.selected_video, self.selected_audio,
                    self.volume_slider.get())
                self.parent.after(0, lambda: self.progress_label.configure(
                    text=f"✅ Saved: {os.path.basename(output)}"))
            except Exception as e:
                self.parent.after(0, lambda: self.progress_label.configure(
                    text=f"❌ Error: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def _add_to_list(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("Video", "*.mp4 *.avi *.mov"), ("All", "*.*")])
        self.video_list.extend(paths)
        self.list_label.configure(text=f"Videos: {len(self.video_list)}")

    def _clear_list(self):
        self.video_list = []
        self.list_label.configure(text="Videos: 0")

    def _combine_videos(self):
        if len(self.video_list) < 2:
            self.progress_label.configure(text="⚠️ Add at least 2 videos!")
            return

        self.progress_label.configure(text="Combining videos...")

        def run():
            try:
                output = self.editor.combine_videos(self.video_list)
                self.parent.after(0, lambda: self.progress_label.configure(
                    text=f"✅ Saved: {os.path.basename(output)}"))
            except Exception as e:
                self.parent.after(0, lambda: self.progress_label.configure(
                    text=f"❌ Error: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def _loop_video(self):
        if not self.selected_video:
            return

        loops = int(self.loop_entry.get())
        self.progress_label.configure(text="Looping video...")

        def run():
            try:
                output = self.editor.loop_video(self.selected_video, loops)
                self.parent.after(0, lambda: self.progress_label.configure(
                    text=f"✅ Saved: {os.path.basename(output)}"))
            except Exception as e:
                self.parent.after(0, lambda: self.progress_label.configure(
                    text=f"❌ Error: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def _change_speed(self, speed):
        if not self.selected_video:
            return

        self.progress_label.configure(text=f"Adjusting speed to {speed}x...")

        def run():
            try:
                output = self.editor.adjust_speed(self.selected_video, speed)
                self.parent.after(0, lambda: self.progress_label.configure(
                    text=f"✅ Saved: {os.path.basename(output)}"))
            except Exception as e:
                self.parent.after(0, lambda: self.progress_label.configure(
                    text=f"❌ Error: {e}"))

        threading.Thread(target=run, daemon=True).start()
