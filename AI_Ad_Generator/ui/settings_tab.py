import customtkinter as ctk
from ui.styles import COLORS, FONTS
from config import MODELS
import threading
import os


class SettingsTab:
    """Settings and model management tab"""

    def __init__(self, parent, model_manager):
        self.parent = parent
        self.model_manager = model_manager
        self._create_ui()

    def _create_ui(self):
        main_frame = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ============ SYSTEM INFO ============
        sys_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_medium"],
                                corner_radius=10)
        sys_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(sys_frame, text="💻 System Information",
                     font=FONTS["heading"]).pack(pady=(15, 10))

        info = self.model_manager.get_system_info()

        info_text = (
            f"Device: {info['device'].upper()}\n"
            f"GPU: {info['gpu_name']}\n"
            f"VRAM: {info['vram_gb']} GB\n"
            f"RAM: {info['ram_gb']} GB\n"
            f"Compatible Models: {len(info['available_models'])}"
        )

        ctk.CTkLabel(sys_frame, text=info_text, font=FONTS["body"],
                    justify="left").pack(padx=20, pady=(0, 15))

        # ============ MODEL MANAGER ============
        models_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_medium"],
                                   corner_radius=10)
        models_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(models_frame, text="📦 Model Manager",
                     font=FONTS["heading"]).pack(pady=(15, 10))

        ctk.CTkLabel(models_frame,
                    text="Download AI models to use for generation. Models are stored locally.",
                    font=FONTS["small"],
                    text_color=COLORS["text_secondary"]).pack(padx=20, pady=(0, 10))

        self.model_widgets = {}

        for key, model in MODELS.items():
            model_frame = ctk.CTkFrame(models_frame, fg_color=COLORS["bg_dark"],
                                      corner_radius=8)
            model_frame.pack(fill="x", padx=15, pady=5)

            # Model info
            left = ctk.CTkFrame(model_frame, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=10, pady=8)

            is_downloaded = self.model_manager.is_model_downloaded(key)
            status_icon = "✅" if is_downloaded else "⬇️"

            ctk.CTkLabel(left, text=f"{status_icon} {model['name']}",
                        font=FONTS["subheading"]).pack(anchor="w")

            details = f"Type: {model['type']} | VRAM: {model['vram']}GB | Repo: {model['repo']}"
            ctk.CTkLabel(left, text=details,
                        font=FONTS["small"],
                        text_color=COLORS["text_secondary"]).pack(anchor="w")

            # Download button
            right = ctk.CTkFrame(model_frame, fg_color="transparent")
            right.pack(side="right", padx=10, pady=8)

            if is_downloaded:
                btn_text = "✅ Downloaded"
                btn_color = COLORS["success"]
                btn_state = "disabled"
            else:
                btn_text = "⬇️ Download"
                btn_color = COLORS["accent"]
                btn_state = "normal"

            btn = ctk.CTkButton(
                right,
                text=btn_text,
                width=120,
                fg_color=btn_color,
                state=btn_state,
                command=lambda k=key: self._download_model(k),
            )
            btn.pack()

            self.model_widgets[key] = btn

        # Progress
        self.dl_progress = ctk.CTkProgressBar(models_frame, progress_color=COLORS["accent"])
        self.dl_progress.pack(fill="x", padx=15, pady=10)
        self.dl_progress.set(0)

        self.dl_label = ctk.CTkLabel(models_frame, text="",
                                    font=FONTS["small"],
                                    text_color=COLORS["text_secondary"])
        self.dl_label.pack(pady=(0, 15))

        # ============ SETTINGS ============
        settings_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_medium"],
                                     corner_radius=10)
        settings_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(settings_frame, text="⚙️ Settings",
                     font=FONTS["heading"]).pack(pady=(15, 10))

        # Output directory
        out_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        out_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(out_frame, text="Output Directory:", font=FONTS["body"]).pack(
            anchor="w")

        out_inner = ctk.CTkFrame(out_frame, fg_color="transparent")
        out_inner.pack(fill="x")

        from config import OUTPUTS_DIR
        self.output_entry = ctk.CTkEntry(out_inner, fg_color=COLORS["entry_bg"])
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.output_entry.insert(0, OUTPUTS_DIR)

        ctk.CTkButton(out_inner, text="📂", width=40,
                      fg_color=COLORS["bg_light"],
                      command=lambda: os.startfile(OUTPUTS_DIR)).pack(side="right")

        # Half precision
        self.fp16_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Use FP16 (faster, less VRAM)",
                       variable=self.fp16_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=20, pady=5)

        # CPU offload
        self.offload_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Enable CPU Offloading",
                       variable=self.offload_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=20, pady=5)

        # Clear cache button
        ctk.CTkButton(
            settings_frame,
            text="🗑️ Clear Temp Files",
            fg_color=COLORS["error"],
            command=self._clear_temp,
        ).pack(fill="x", padx=15, pady=15)

    def _download_model(self, model_key):
        btn = self.model_widgets[model_key]
        btn.configure(state="disabled", text="⏳ Downloading...")

        def run():
            try:
                def progress(value, msg):
                    self.parent.after(0, lambda: self.dl_progress.set(value / 100))
                    self.parent.after(0, lambda: self.dl_label.configure(text=msg))

                self.model_manager.download_model(model_key, progress)

                self.parent.after(0, lambda: btn.configure(
                    text="✅ Downloaded", fg_color=COLORS["success"]))
            except Exception as e:
                self.parent.after(0, lambda: btn.configure(
                    text="❌ Failed", fg_color=COLORS["error"], state="normal"))
                self.parent.after(0, lambda: self.dl_label.configure(
                    text=f"Error: {str(e)}"))

        threading.Thread(target=run, daemon=True).start()

    def _clear_temp(self):
        from config import TEMP_DIR
        import shutil
        try:
            shutil.rmtree(TEMP_DIR)
            os.makedirs(TEMP_DIR)
            self.dl_label.configure(text="✅ Temp files cleared!")
        except Exception as e:
            self.dl_label.configure(text=f"Error: {e}")
