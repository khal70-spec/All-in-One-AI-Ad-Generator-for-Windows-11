import customtkinter as ctk
from ui.styles import COLORS, FONTS
from core.text_to_video import TextToVideoGenerator
from config import AD_TEMPLATES
import threading
import os


class TextToVideoTab:
    """Text to Video generation tab"""

    def __init__(self, parent, model_manager, prompt_generator):
        self.parent = parent
        self.model_manager = model_manager
        self.prompt_generator = prompt_generator
        self.generator = TextToVideoGenerator(model_manager)
        self.is_generating = False

        self._create_ui()

    def _create_ui(self):
        # Main container with two columns
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ============ LEFT PANEL - SETTINGS ============
        left_panel = ctk.CTkScrollableFrame(main_frame, width=400,
                                           fg_color=COLORS["bg_medium"],
                                           corner_radius=10)
        left_panel.pack(side="left", fill="y", padx=(0, 10), pady=0)

        # Title
        ctk.CTkLabel(left_panel, text="⚡ Text to Video",
                     font=FONTS["heading"]).pack(pady=(10, 5))

        # Model Selection
        ctk.CTkLabel(left_panel, text="Select Model:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(10, 0))

        self.model_var = ctk.StringVar(value="zeroscope")
        model_menu = ctk.CTkOptionMenu(
            left_panel,
            variable=self.model_var,
            values=["zeroscope", "cogvideox", "modelscope",
                    "mochi", "hunyuanvideo", "ltx_video"],
            fg_color=COLORS["entry_bg"],
            button_color=COLORS["accent"],
        )
        model_menu.pack(fill="x", padx=10, pady=5)

        # Ad Template
        ctk.CTkLabel(left_panel, text="Ad Template:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(10, 0))

        template_names = ["Custom"] + [t["name"] for t in AD_TEMPLATES.values()]
        self.template_var = ctk.StringVar(value="Custom")
        template_menu = ctk.CTkOptionMenu(
            left_panel,
            variable=self.template_var,
            values=template_names,
            command=self._on_template_change,
            fg_color=COLORS["entry_bg"],
            button_color=COLORS["accent"],
        )
        template_menu.pack(fill="x", padx=10, pady=5)

        # Product Name
        ctk.CTkLabel(left_panel, text="Product Name:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(10, 0))

        self.product_entry = ctk.CTkEntry(
            left_panel,
            placeholder_text="e.g., Nike Air Max sneakers",
            fg_color=COLORS["entry_bg"],
            height=35,
        )
        self.product_entry.pack(fill="x", padx=10, pady=5)

        # Prompt
        ctk.CTkLabel(left_panel, text="Prompt:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(10, 0))

        self.prompt_text = ctk.CTkTextbox(
            left_panel, height=100,
            fg_color=COLORS["entry_bg"],
        )
        self.prompt_text.pack(fill="x", padx=10, pady=5)

        # Auto-generate prompt button
        auto_btn = ctk.CTkButton(
            left_panel,
            text="🤖 Auto-Generate Prompt",
            command=self._auto_generate_prompt,
            fg_color=COLORS["bg_light"],
            hover_color=COLORS["accent"],
        )
        auto_btn.pack(fill="x", padx=10, pady=5)

        # Negative Prompt
        ctk.CTkLabel(left_panel, text="Negative Prompt:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(10, 0))

        self.negative_text = ctk.CTkTextbox(
            left_panel, height=60,
            fg_color=COLORS["entry_bg"],
        )
        self.negative_text.pack(fill="x", padx=10, pady=5)
        self.negative_text.insert("0.0", self.prompt_generator.generate_negative_prompt())

        # Settings Frame
        settings_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        settings_frame.pack(fill="x", padx=10, pady=10)

        # Steps
        ctk.CTkLabel(settings_frame, text="Steps:", font=FONTS["body"]).grid(
            row=0, column=0, sticky="w", pady=2)
        self.steps_slider = ctk.CTkSlider(settings_frame, from_=10, to=50, number_of_steps=40)
        self.steps_slider.set(25)
        self.steps_slider.grid(row=0, column=1, padx=10, sticky="ew")
        self.steps_label = ctk.CTkLabel(settings_frame, text="25", width=30)
        self.steps_label.grid(row=0, column=2)
        self.steps_slider.configure(command=lambda v: self.steps_label.configure(text=str(int(v))))

        # Guidance
        ctk.CTkLabel(settings_frame, text="Guidance:", font=FONTS["body"]).grid(
            row=1, column=0, sticky="w", pady=2)
        self.guidance_slider = ctk.CTkSlider(settings_frame, from_=1, to=20, number_of_steps=38)
        self.guidance_slider.set(7.5)
        self.guidance_slider.grid(row=1, column=1, padx=10, sticky="ew")
        self.guidance_label = ctk.CTkLabel(settings_frame, text="7.5", width=30)
        self.guidance_label.grid(row=1, column=2)
        self.guidance_slider.configure(
            command=lambda v: self.guidance_label.configure(text=f"{v:.1f}"))

        # Frames
        ctk.CTkLabel(settings_frame, text="Frames:", font=FONTS["body"]).grid(
            row=2, column=0, sticky="w", pady=2)
        self.frames_slider = ctk.CTkSlider(settings_frame, from_=8, to=48, number_of_steps=40)
        self.frames_slider.set(24)
        self.frames_slider.grid(row=2, column=1, padx=10, sticky="ew")
        self.frames_label = ctk.CTkLabel(settings_frame, text="24", width=30)
        self.frames_label.grid(row=2, column=2)
        self.frames_slider.configure(
            command=lambda v: self.frames_label.configure(text=str(int(v))))

        # Resolution
        ctk.CTkLabel(settings_frame, text="Size:", font=FONTS["body"]).grid(
            row=3, column=0, sticky="w", pady=2)
        self.size_var = ctk.StringVar(value="512x512")
        size_menu = ctk.CTkOptionMenu(
            settings_frame,
            variable=self.size_var,
            values=["256x256", "384x384", "512x512", "576x320", "320x576"],
            fg_color=COLORS["entry_bg"],
        )
        size_menu.grid(row=3, column=1, columnspan=2, padx=10, sticky="ew", pady=2)

        settings_frame.columnconfigure(1, weight=1)

        # Seed
        seed_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        seed_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(seed_frame, text="Seed:", font=FONTS["body"]).pack(side="left")
        self.seed_entry = ctk.CTkEntry(seed_frame, width=100, fg_color=COLORS["entry_bg"])
        self.seed_entry.pack(side="left", padx=10)
        self.seed_entry.insert(0, "-1")
        ctk.CTkLabel(seed_frame, text="(-1 = random)",
                     font=FONTS["small"], text_color=COLORS["text_secondary"]).pack(side="left")

        # ============ SOUND ============
        ctk.CTkLabel(left_panel, text="🔊 Sound:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(10, 0))
        self.sound_voice_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_panel, text="Voiceover (from prompt)",
                       variable=self.sound_voice_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=25, pady=2)
        self.sound_music_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_panel, text="Background music",
                       variable=self.sound_music_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=25, pady=2)

        # ============ GENERATE BUTTON ============
        self.generate_btn = ctk.CTkButton(
            left_panel,
            text="🚀 GENERATE VIDEO",
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

        ctk.CTkLabel(right_panel, text="📺 Preview",
                     font=FONTS["heading"]).pack(pady=10)

        self.preview_frame = ctk.CTkFrame(right_panel, fg_color=COLORS["bg_dark"],
                                         width=512, height=512, corner_radius=10)
        self.preview_frame.pack(expand=True, padx=20, pady=10)
        self.preview_frame.pack_propagate(False)

        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="Generated video will appear here\n\n🎬",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
        )
        self.preview_label.pack(expand=True)

        # Output path
        self.output_label = ctk.CTkLabel(
            right_panel,
            text="",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
        )
        self.output_label.pack(pady=5)

        # Action buttons
        btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="📂 Open Output Folder",
                      command=self._open_output_folder,
                      fg_color=COLORS["bg_light"]).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="▶️ Play Video",
                      command=self._play_video,
                      fg_color=COLORS["bg_light"]).pack(side="left", padx=5)

    def _auto_generate_prompt(self):
        product = self.product_entry.get()
        if not product:
            product = "product"

        prompt = self.prompt_generator.generate_prompt(product)
        self.prompt_text.delete("0.0", "end")
        self.prompt_text.insert("0.0", prompt)

    def _on_template_change(self, template_name):
        for key, template in AD_TEMPLATES.items():
            if template["name"] == template_name:
                product = self.product_entry.get() or "product"
                prompt = template["prompt_template"].format(product=product)
                self.prompt_text.delete("0.0", "end")
                self.prompt_text.insert("0.0", prompt)

                self.negative_text.delete("0.0", "end")
                self.negative_text.insert("0.0", template["negative"])

                self.steps_slider.set(template["steps"])
                self.guidance_slider.set(template["guidance"])
                break

    def _get_seed(self):
        """Parse the seed entry safely; -1 (random) on invalid input."""
        try:
            return int(self.seed_entry.get().strip())
        except (ValueError, AttributeError):
            return -1

    def _generate(self):
        if self.is_generating:
            return

        prompt = self.prompt_text.get("0.0", "end").strip()
        if not prompt:
            self.progress_label.configure(text="⚠️ Please enter a prompt!")
            return

        # Snapshot all widget values on the UI thread (tkinter is not
        # thread-safe, so the worker must not read widgets directly).
        size = self.size_var.get().split("x")
        width, height = int(size[0]), int(size[1])
        negative = self.negative_text.get("0.0", "end").strip()
        num_frames = int(self.frames_slider.get())
        num_steps = int(self.steps_slider.get())
        guidance = float(self.guidance_slider.get())
        seed = self._get_seed()
        model = self.model_var.get()

        self.is_generating = True
        self.generate_btn.configure(state="disabled", text="⏳ Generating...")

        def run():
            try:
                output = self.generator.generate(
                    prompt=prompt,
                    negative_prompt=negative,
                    num_frames=num_frames,
                    width=width,
                    height=height,
                    num_steps=num_steps,
                    guidance_scale=guidance,
                    seed=seed,
                    model=model,
                    progress_callback=self._update_progress,
                )

                self.parent.after(0, lambda: self._on_complete(output))

            except Exception as e:
                local_err = str(e)
                # Optional cloud fallback when local generation fails
                from config import USER_SETTINGS
                if USER_SETTINGS.get("use_online_fallback") and prompt:
                    try:
                        from core.online_apis import try_fallback
                        self._update_progress(0, "Local failed — trying cloud...")
                        out = try_fallback(prompt=prompt,
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
        self.generate_btn.configure(state="normal", text="🚀 GENERATE VIDEO")
        self.progress_bar.set(1)
        self.progress_label.configure(text="✅ Generation complete!")
        self.output_label.configure(text=f"Saved: {output_path}")
        self.last_output = output_path

        # Show a thumbnail of the result
        try:
            from core.preview_utils import make_ctk_thumbnail
            photo = make_ctk_thumbnail(output_path)
            if photo is not None:
                self.preview_label.configure(image=photo, text="")
                self.preview_label.image = photo
        except Exception as e:
            print(f"Preview error: {e}")

        # Optional sound (voiceover + background music)
        voice = self.sound_voice_var.get()
        music = self.sound_music_var.get()
        if voice or music:
            self.progress_label.configure(text="🔊 Adding sound...")
            prompt = self.prompt_text.get("0.0", "end").strip()
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
                self.preview_label.configure(image=photo, text="")
                self.preview_label.image = photo
        except Exception:
            pass

    def _on_error(self, error):
        self.is_generating = False
        self.generate_btn.configure(state="normal", text="🚀 GENERATE VIDEO")
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"❌ Error: {error}")

    def _open_output_folder(self):
        from config import OUTPUTS_DIR
        os.startfile(OUTPUTS_DIR)

    def _play_video(self):
        if hasattr(self, 'last_output') and os.path.exists(self.last_output):
            os.startfile(self.last_output)
