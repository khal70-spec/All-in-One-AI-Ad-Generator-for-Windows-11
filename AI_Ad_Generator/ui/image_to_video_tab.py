import customtkinter as ctk
from ui.styles import COLORS, FONTS
from core.image_to_video import ImageToVideoGenerator
from core.background_remover import BackgroundRemover
from core.image_editor import ImageEditor
from core.text_to_image import TextToImageGenerator
from core.upscaler import UpscalerClient
from PIL import Image, ImageTk
from tkinter import filedialog
import threading
import os


class ImageToVideoTab:
    """Image to Video generation tab"""

    def __init__(self, parent, model_manager):
        self.parent = parent
        self.model_manager = model_manager
        self.generator = ImageToVideoGenerator(model_manager)
        self.bg_remover = BackgroundRemover()
        self.image_editor = ImageEditor()
        self.t2i = TextToImageGenerator(model_manager)
        self.upscaler = UpscalerClient()
        self.selected_image = None
        self.is_generating = False
        self.is_img_gen = False

        self._create_ui()

    def _create_ui(self):
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ============ LEFT PANEL ============
        left_panel = ctk.CTkScrollableFrame(main_frame, width=400,
                                          fg_color=COLORS["bg_medium"],
                                          corner_radius=10)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        ctk.CTkLabel(left_panel, text="🖼 Image to Video",
                     font=FONTS["heading"]).pack(pady=(10, 5))

        # Image Selection
        self.select_btn = ctk.CTkButton(
            left_panel,
            text="📁 Select Product Image",
            font=FONTS["button"],
            height=45,
            fg_color=COLORS["bg_light"],
            hover_color=COLORS["accent"],
            command=self._select_image,
        )
        self.select_btn.pack(fill="x", padx=10, pady=10)

        # Image Preview
        self.image_preview = ctk.CTkFrame(left_panel, fg_color=COLORS["bg_dark"],
                                         height=200, corner_radius=10)
        self.image_preview.pack(fill="x", padx=10, pady=5)
        self.image_preview.pack_propagate(False)

        self.image_label = ctk.CTkLabel(
            self.image_preview,
            text="No image selected",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
        )
        self.image_label.pack(expand=True)

        # Generate Image (SDXL)
        ctk.CTkLabel(left_panel, text="Or generate an image with AI:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(10, 0))

        self.gen_prompt_entry = ctk.CTkEntry(
            left_panel,
            placeholder_text="Describe the product image to create...",
            fg_color=COLORS["entry_bg"],
        )
        self.gen_prompt_entry.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            left_panel,
            text="🎨 Generate Image (SDXL)",
            height=38,
            fg_color=COLORS["bg_light"],
            hover_color=COLORS["accent"],
            command=self._generate_base_image,
        ).pack(fill="x", padx=10, pady=(0, 5))

        # Image Processing Options
        ctk.CTkLabel(left_panel, text="Image Processing:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(15, 5))

        self.remove_bg_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(left_panel, text="Remove Background",
                       variable=self.remove_bg_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=20, pady=2)

        self.enhance_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_panel, text="Enhance Image",
                       variable=self.enhance_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=20, pady=2)

        self.upscale_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(left_panel, text="Upscale first (free online)",
                       variable=self.upscale_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=20, pady=2)

        # Model Selection
        ctk.CTkLabel(left_panel, text="Model:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(15, 5))

        self.model_var = ctk.StringVar(value="svd")
        model_menu = ctk.CTkOptionMenu(
            left_panel,
            variable=self.model_var,
            values=["svd", "animatediff", "online (Pika/Luma)"],
            fg_color=COLORS["entry_bg"],
            button_color=COLORS["accent"],
        )
        model_menu.pack(fill="x", padx=10, pady=5)

        self.provider_var = ctk.StringVar(value="pika")
        ctk.CTkOptionMenu(
            left_panel,
            variable=self.provider_var,
            values=["pika", "luma"],
            fg_color=COLORS["entry_bg"],
            button_color=COLORS["accent"],
        ).pack(fill="x", padx=10, pady=5)

        # ============ SOUND ============
        ctk.CTkLabel(left_panel, text="🔊 Sound:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(10, 0))
        self.sound_voice_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_panel, text="Voiceover (from prompt above)",
                       variable=self.sound_voice_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=25, pady=2)
        self.sound_music_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_panel, text="Background music",
                       variable=self.sound_music_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=25, pady=2)

        # Settings
        settings_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        settings_frame.pack(fill="x", padx=10, pady=10)

        # Frames
        ctk.CTkLabel(settings_frame, text="Frames:", font=FONTS["body"]).grid(
            row=0, column=0, sticky="w", pady=2)
        self.frames_slider = ctk.CTkSlider(settings_frame, from_=8, to=48, number_of_steps=40)
        self.frames_slider.set(25)
        self.frames_slider.grid(row=0, column=1, padx=10, sticky="ew")
        self.frames_lbl = ctk.CTkLabel(settings_frame, text="25", width=30)
        self.frames_lbl.grid(row=0, column=2)
        self.frames_slider.configure(
            command=lambda v: self.frames_lbl.configure(text=str(int(v))))

        # Motion Amount
        ctk.CTkLabel(settings_frame, text="Motion:", font=FONTS["body"]).grid(
            row=1, column=0, sticky="w", pady=2)
        self.motion_slider = ctk.CTkSlider(settings_frame, from_=0, to=255, number_of_steps=255)
        self.motion_slider.set(127)
        self.motion_slider.grid(row=1, column=1, padx=10, sticky="ew")
        self.motion_lbl = ctk.CTkLabel(settings_frame, text="127", width=30)
        self.motion_lbl.grid(row=1, column=2)
        self.motion_slider.configure(
            command=lambda v: self.motion_lbl.configure(text=str(int(v))))

        # Noise
        ctk.CTkLabel(settings_frame, text="Noise:", font=FONTS["body"]).grid(
            row=2, column=0, sticky="w", pady=2)
        self.noise_slider = ctk.CTkSlider(settings_frame, from_=0, to=0.1, number_of_steps=100)
        self.noise_slider.set(0.02)
        self.noise_slider.grid(row=2, column=1, padx=10, sticky="ew")
        self.noise_lbl = ctk.CTkLabel(settings_frame, text="0.02", width=40)
        self.noise_lbl.grid(row=2, column=2)
        self.noise_slider.configure(
            command=lambda v: self.noise_lbl.configure(text=f"{v:.2f}"))

        settings_frame.columnconfigure(1, weight=1)

        # Seed
        seed_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        seed_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(seed_frame, text="Seed:", font=FONTS["body"]).pack(side="left")
        self.seed_entry = ctk.CTkEntry(seed_frame, width=100, fg_color=COLORS["entry_bg"])
        self.seed_entry.pack(side="left", padx=10)
        self.seed_entry.insert(0, "-1")

        # Generate Button
        self.generate_btn = ctk.CTkButton(
            left_panel,
            text="🚀 ANIMATE IMAGE",
            font=FONTS["button"],
            height=50,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._generate,
        )
        self.generate_btn.pack(fill="x", padx=10, pady=15)

        # Progress
        self.progress_bar = ctk.CTkProgressBar(left_panel, progress_color=COLORS["accent"])
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            left_panel, text="Ready",
            font=FONTS["small"], text_color=COLORS["text_secondary"],
        )
        self.progress_label.pack(padx=10, pady=(0, 10))

        # ============ RIGHT PANEL - PREVIEW ============
        right_panel = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_medium"],
                                  corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(right_panel, text="📺 Video Preview",
                     font=FONTS["heading"]).pack(pady=10)

        self.video_preview = ctk.CTkFrame(right_panel, fg_color=COLORS["bg_dark"],
                                        width=512, height=512, corner_radius=10)
        self.video_preview.pack(expand=True, padx=20, pady=10)
        self.video_preview.pack_propagate(False)

        self.video_label = ctk.CTkLabel(
            self.video_preview,
            text="Generated video will appear here\n\n🎬",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
        )
        self.video_label.pack(expand=True)

        self.output_label = ctk.CTkLabel(right_panel, text="",
                                        font=FONTS["small"],
                                        text_color=COLORS["text_secondary"])
        self.output_label.pack(pady=5)

        btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="📂 Open Folder",
                      command=self._open_output,
                      fg_color=COLORS["bg_light"]).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="▶️ Play",
                      command=self._play_video,
                      fg_color=COLORS["bg_light"]).pack(side="left", padx=5)

    def _select_image(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.webp *.bmp"),
                ("All files", "*.*"),
            ]
        )
        if path:
            self.selected_image = path
            self._show_image_preview(path)

    def _show_image_preview(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((380, 180))
            photo = ctk.CTkImage(light_image=img, dark_image=img,
                                size=(img.width, img.height))
            self.image_label.configure(image=photo, text="")
            self.image_label.image = photo
        except Exception as e:
            self.image_label.configure(text=f"Error: {e}")

    def _generate_base_image(self):
        prompt = self.gen_prompt_entry.get().strip()
        if not prompt:
            self.progress_label.configure(text="⚠️ Enter a description first!")
            return
        if self.is_img_gen:
            return

        self.is_img_gen = True
        self.progress_label.configure(text="🎨 Generating image...")

        def run():
            try:
                out = self.t2i.generate(prompt=prompt, progress_callback=self._update_progress)
                self.selected_image = out
                self.parent.after(0, lambda: self._show_image_preview(out))
                self.parent.after(0, lambda: self.progress_label.configure(
                    text=f"✅ Image ready: {os.path.basename(out)}"))
            except Exception as e:
                msg = str(e)
                self.parent.after(0, lambda m=msg: self.progress_label.configure(
                    text=f"❌ Image error: {m}"))
            finally:
                self.is_img_gen = False

        threading.Thread(target=run, daemon=True).start()

    def _get_seed(self):
        """Parse the seed entry safely; -1 (random) on invalid input."""
        try:
            return int(self.seed_entry.get().strip())
        except (ValueError, AttributeError):
            return -1

    def _generate(self):
        if self.is_generating or not self.selected_image:
            if not self.selected_image:
                self.progress_label.configure(text="⚠️ Please select an image first!")
            return

        # Snapshot all widget values on the UI thread (tkinter is not
        # thread-safe, so the worker must not read widgets directly).
        model = self.model_var.get()
        provider_key = self.provider_var.get()
        prompt = (self.gen_prompt_entry.get().strip()
                 or "product advertisement, smooth motion, professional")
        remove_bg = self.remove_bg_var.get()
        enhance = self.enhance_var.get()
        upscale = self.upscale_var.get()
        num_frames = int(self.frames_slider.get())
        motion = int(self.motion_slider.get())
        noise = float(self.noise_slider.get())
        seed = self._get_seed()
        source_image = self.selected_image

        self.is_generating = True
        self.generate_btn.configure(state="disabled", text="⏳ Generating...")

        def run():
            try:
                # ---- Online image-to-video (Pika / Luma) ----
                if model == "online (Pika/Luma)":
                    self._update_progress(5, "Submitting to cloud provider...")
                    from core.online_apis import get_provider
                    provider = get_provider(provider_key)
                    out = provider.generate(
                        prompt=prompt,
                        image_path=source_image,
                        progress_callback=self._update_progress,
                    )
                    self.parent.after(0, lambda: self._on_complete(out))
                    return

                image_path = source_image

                # Process image
                if remove_bg:
                    self._update_progress(5, "Removing background...")
                    image_path = self.bg_remover.remove_background(image_path)

                if enhance:
                    self._update_progress(10, "Enhancing image...")
                    image_path = self.image_editor.enhance_image(
                        image_path, brightness=1.05, contrast=1.1, sharpness=1.2)

                if upscale:
                    self._update_progress(15, "Upscaling image (online)...")
                    image_path = self.upscaler.upscale_image(image_path)

                output = self.generator.generate_from_image(
                    image_path=image_path,
                    num_frames=num_frames,
                    motion_bucket_id=motion,
                    noise_aug=noise,
                    seed=seed,
                    model=model,
                    progress_callback=self._update_progress,
                )

                self.parent.after(0, lambda: self._on_complete(output))

            except Exception as e:
                local_err = str(e)
                # Optional cloud fallback when local generation fails
                from config import USER_SETTINGS
                if (USER_SETTINGS.get("use_online_fallback")
                        and model != "online (Pika/Luma)"
                        and source_image):
                    try:
                        from core.online_apis import try_fallback
                        self._update_progress(0, "Local failed — trying cloud...")
                        out = try_fallback(prompt=prompt,
                                          image_path=source_image,
                                          progress_callback=self._update_progress)
                        self.parent.after(0, lambda: self._on_complete(out))
                        return
                    except Exception as fe:
                        cloud_err = str(fe)
                        self.parent.after(0, lambda m=f"Local: {local_err}\nCloud: {cloud_err}":
                                          self._on_error(m))
                        return
                self.parent.after(0, lambda m=local_err: self._on_error(m))

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _update_progress(self, value, message):
        self.parent.after(0, lambda: self.progress_bar.set(value / 100))
        self.parent.after(0, lambda: self.progress_label.configure(text=message))

    def _on_complete(self, output_path):
        self.is_generating = False
        self.generate_btn.configure(state="normal", text="🚀 ANIMATE IMAGE")
        self.progress_bar.set(1)
        self.progress_label.configure(text="✅ Complete!")
        self.output_label.configure(text=f"Saved: {output_path}")
        self.last_output = output_path

        # Show a thumbnail of the result
        try:
            from core.preview_utils import make_ctk_thumbnail
            photo = make_ctk_thumbnail(output_path)
            if photo is not None:
                self.video_label.configure(image=photo, text="")
                self.video_label.image = photo
        except Exception as e:
            print(f"Preview error: {e}")

        # Optional sound (voiceover + background music)
        voice = self.sound_voice_var.get()
        music = self.sound_music_var.get()
        if voice or music:
            self.progress_label.configure(text="🔊 Adding sound...")
            prompt = self.gen_prompt_entry.get().strip()
            threading.Thread(target=self._add_sound,
                            args=(output_path, prompt, voice, music),
                            daemon=True).start()

    def _add_sound(self, video_path, prompt, voiceover, music):
        try:
            from core.sound import add_sound_to_video
            out = add_sound_to_video(
                video_path, prompt=prompt,
                voiceover=voiceover,
                music=music)
            if out and os.path.exists(out):
                self.last_output = out
                self.parent.after(0, lambda: self._refresh_preview(out))
                self.parent.after(
                    0, lambda: self.progress_label.configure(
                        text="✅ Done — video with sound!"))
                return
        except Exception as e:
            print(f"Sound error: {e}")
        self.parent.after(
            0, lambda: self.progress_label.configure(
                text="✅ Video ready (sound skipped)"))

    def _refresh_preview(self, video_path):
        """Update the preview thumbnail. Must run on the UI thread."""
        try:
            from core.preview_utils import make_ctk_thumbnail
            photo = make_ctk_thumbnail(video_path)
            if photo is not None:
                self.video_label.configure(image=photo, text="")
                self.video_label.image = photo
        except Exception:
            pass

    def _on_error(self, error):
        self.is_generating = False
        self.generate_btn.configure(state="normal", text="🚀 ANIMATE IMAGE")
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"❌ Error: {error}")

    def _open_output(self):
        from config import OUTPUTS_DIR
        os.startfile(OUTPUTS_DIR)

    def _play_video(self):
        if hasattr(self, 'last_output') and os.path.exists(self.last_output):
            os.startfile(self.last_output)
