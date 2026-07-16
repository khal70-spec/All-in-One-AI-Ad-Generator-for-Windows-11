import customtkinter as ctk
from ui.styles import COLORS, FONTS
from config import MODELS, USER_SETTINGS, save_settings, ONLINE_PROVIDERS
from core.webhook_server import WebhookReceiver
from core.utils import open_path
import threading
import os


class SettingsTab:
    """Settings and model management tab"""

    def __init__(self, parent, model_manager):
        self.parent = parent
        self.model_manager = model_manager
        self.webhook = None
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
        self.models_container = ctk.CTkFrame(models_frame, fg_color="transparent")
        self.models_container.pack(fill="x")
        self._refresh_model_rows()

        # Progress
        self.dl_progress = ctk.CTkProgressBar(models_frame, progress_color=COLORS["accent"])
        self.dl_progress.pack(fill="x", padx=15, pady=10)
        self.dl_progress.set(0)

        self.dl_label = ctk.CTkLabel(models_frame, text="",
                                    font=FONTS["small"],
                                    text_color=COLORS["text_secondary"])
        self.dl_label.pack(pady=(0, 2))

        self.disk_label = ctk.CTkLabel(models_frame,
                                      text=self._disk_text(),
                                      font=FONTS["small"],
                                      text_color=COLORS["text_secondary"])
        self.disk_label.pack(pady=(0, 15))

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
                      command=lambda: open_path(OUTPUTS_DIR)).pack(side="right")

        # Precision / offload are applied automatically by the model loaders
        # (FP16 on CUDA, FP32 on CPU; CPU offloading whenever a GPU is
        # available). Shown as info rather than fake toggles.
        ctk.CTkLabel(
            settings_frame,
            text="ℹ️ FP16 precision is used automatically on CUDA GPUs "
                 "(FP32 on CPU).",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
            justify="left",
        ).pack(anchor="w", padx=20, pady=(5, 0))

        ctk.CTkLabel(
            settings_frame,
            text="ℹ️ Model CPU offloading is enabled automatically when a "
                 "GPU is detected to save VRAM.",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 5))

        # Clear cache button
        ctk.CTkButton(
            settings_frame,
            text="🗑️ Clear Temp Files",
            fg_color=COLORS["error"],
            command=self._clear_temp,
        ).pack(fill="x", padx=15, pady=15)

        # ============ ONLINE APIS ============
        api_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_medium"],
                               corner_radius=10)
        api_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(api_frame, text="🌐 Online APIs (Pika / Luma)",
                     font=FONTS["heading"]).pack(pady=(15, 5))

        ctk.CTkLabel(api_frame,
                     text="Optional. Add API keys to generate videos in the cloud "
                          "when no GPU is available. Keys are stored locally in config.json.",
                     font=FONTS["small"],
                     text_color=COLORS["text_secondary"]).pack(padx=20, pady=(0, 10))

        self.api_entries = {}
        for key, prov in ONLINE_PROVIDERS.items():
            row = ctk.CTkFrame(api_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=4)
            ctk.CTkLabel(row, text=f"{prov['name']} API Key:",
                        font=FONTS["body"], width=160, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, fg_color=COLORS["entry_bg"], show="*")
            entry.insert(0, USER_SETTINGS.get(f"{key}_api_key", ""))
            entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
            self.api_entries[key] = entry

        self.fallback_var = ctk.BooleanVar(
            value=USER_SETTINGS.get("use_online_fallback", False))
        ctk.CTkCheckBox(
            api_frame,
            text="Use cloud fallback if local generation fails",
            variable=self.fallback_var,
            fg_color=COLORS["accent"],
        ).pack(anchor="w", padx=15, pady=(5, 0))

        ctk.CTkButton(
            api_frame,
            text="💾 Save API Keys",
            fg_color=COLORS["accent"],
            command=self._save_api_keys,
        ).pack(fill="x", padx=15, pady=(10, 15))

        # ============ WEBHOOK RECEIVER ============
        wh_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_medium"],
                               corner_radius=10)
        wh_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(wh_frame, text="🔔 Webhook Receiver",
                     font=FONTS["heading"]).pack(pady=(15, 5))

        ctk.CTkLabel(wh_frame,
                     text="Start a local server to receive Pika/Luma completion "
                          "callbacks. Use its URL as the webhook_url when generating "
                          "online (expose it via ngrok/LAN for cloud providers).",
                     font=FONTS["small"],
                     text_color=COLORS["text_secondary"]).pack(padx=20, pady=(0, 10))

        row = ctk.CTkFrame(wh_frame, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(row, text="Port:", font=FONTS["body"]).pack(side="left")
        self.wh_port = ctk.CTkEntry(row, width=80, fg_color=COLORS["entry_bg"])
        self.wh_port.insert(0, "8000")
        self.wh_port.pack(side="left", padx=10)
        self.wh_start = ctk.CTkButton(row, text="▶ Start", width=90,
                                    fg_color=COLORS["success"],
                                    command=self._start_webhook)
        self.wh_start.pack(side="left", padx=5)
        self.wh_stop = ctk.CTkButton(row, text="■ Stop", width=90,
                                   fg_color=COLORS["error"],
                                   command=self._stop_webhook, state="disabled")
        self.wh_stop.pack(side="left", padx=5)

        self.wh_url = ctk.CTkLabel(wh_frame, text="URL: (not started)",
                                  font=FONTS["small"],
                                  text_color=COLORS["text_secondary"])
        self.wh_url.pack(padx=15, pady=(0, 5))

        self.wh_log = ctk.CTkTextbox(wh_frame, height=90,
                                    fg_color=COLORS["bg_dark"],
                                    font=("Consolas", 10))
        self.wh_log.pack(fill="x", padx=15, pady=(0, 15))

    def _wh_log(self, msg):
        # Called from the HTTP server thread — marshal widget updates onto
        # the UI thread (tkinter is not thread-safe).
        def _append():
            self.wh_log.insert("end", msg + "\n")
            self.wh_log.see("end")
        try:
            self.parent.after(0, _append)
        except Exception:
            pass

    def _start_webhook(self):
        try:
            port = int(self.wh_port.get())
        except ValueError:
            self.wh_url.configure(text="URL: invalid port")
            return
        if self.webhook is None:
            self.webhook = WebhookReceiver(port=port, log_callback=self._wh_log)
        else:
            self.webhook.port = port
        self.webhook.start()
        self.wh_url.configure(text=f"URL: {self.webhook.url} (expose via ngrok/LAN)")
        self.wh_start.configure(state="disabled")
        self.wh_stop.configure(state="normal")
        self._wh_log("Webhook receiver started.")

    def _stop_webhook(self):
        if self.webhook is not None:
            self.webhook.stop()
        self.wh_start.configure(state="normal")
        self.wh_stop.configure(state="disabled")
        self.wh_url.configure(text="URL: (stopped)")
        self._wh_log("Webhook receiver stopped.")

    def _save_api_keys(self):
        for key, entry in self.api_entries.items():
            USER_SETTINGS[f"{key}_api_key"] = entry.get().strip()
        USER_SETTINGS["use_online_fallback"] = self.fallback_var.get()
        save_settings()
        self.dl_label.configure(text="✅ API keys saved to config.json")

    # ------------------------------------------------------------------ #
    # Model manager helpers
    # ------------------------------------------------------------------ #
    def _disk_text(self):
        try:
            free = self.model_manager.disk_free_gb()
        except Exception:
            free = None
        return f"💾 Free disk space: {free:.1f} GB" if free is not None else ""

    def _refresh_model_rows(self):
        """Rebuild the model list rows (status, size, download/delete)."""
        for w in self.models_container.winfo_children():
            w.destroy()
        self.model_widgets = {}

        for key, model in MODELS.items():
            model_frame = ctk.CTkFrame(self.models_container,
                                      fg_color=COLORS["bg_dark"],
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

            est = self.model_manager.estimated_size_gb(key)
            if is_downloaded:
                size_txt = f"On disk: {self.model_manager.model_size_label(key)}"
            elif est:
                size_txt = f"Download size: ≈{est} GB"
            else:
                size_txt = ""
            if size_txt:
                ctk.CTkLabel(left, text=size_txt,
                            font=FONTS["small"],
                            text_color=COLORS["text_secondary"]).pack(anchor="w")

            # Action buttons
            right = ctk.CTkFrame(model_frame, fg_color="transparent")
            right.pack(side="right", padx=10, pady=8)

            if is_downloaded:
                done = ctk.CTkLabel(right, text="✅ Installed",
                                    font=FONTS["body"],
                                    text_color=COLORS["success"])
                done.pack(side="left", padx=(0, 8))
                btn = ctk.CTkButton(
                    right, text="🗑 Delete", width=100,
                    fg_color=COLORS["error"],
                    command=lambda k=key: self._delete_model(k),
                )
            else:
                btn = ctk.CTkButton(
                    right, text="⬇️ Download", width=120,
                    fg_color=COLORS["accent"],
                    command=lambda k=key: self._download_model(k),
                )
            btn.pack()
            self.model_widgets[key] = btn

        if hasattr(self, "disk_label"):
            self.disk_label.configure(text=self._disk_text())

    def _delete_model(self, model_key):
        btn = self.model_widgets.get(model_key)
        if btn is not None:
            btn.configure(state="disabled", text="⏳ Deleting...")
        self.dl_label.configure(text=f"Deleting {MODELS[model_key]['name']}...")

        def run():
            try:
                self.model_manager.delete_model(model_key)
                self.parent.after(0, lambda: self.dl_label.configure(
                    text=f"🗑 Deleted {MODELS[model_key]['name']}"))
            except Exception as e:
                msg = str(e)
                self.parent.after(0, lambda m=msg: self.dl_label.configure(
                    text=f"Delete error: {m}"))
            finally:
                self.parent.after(0, self._refresh_model_rows)

        threading.Thread(target=run, daemon=True).start()

    def _download_model(self, model_key):
        btn = self.model_widgets.get(model_key)
        if btn is not None:
            btn.configure(state="disabled", text="⏳ Downloading...")

        def run():
            try:
                def progress(value, msg):
                    self.parent.after(0, lambda: self.dl_progress.set(value / 100))
                    self.parent.after(0, lambda: self.dl_label.configure(text=msg))

                self.model_manager.download_model(model_key, progress)

                self.parent.after(0, self._refresh_model_rows)
            except Exception as e:
                msg = str(e)
                self.parent.after(0, lambda: btn.configure(
                    text="❌ Failed", fg_color=COLORS["error"], state="normal")
                    if btn is not None else None)
                self.parent.after(0, lambda m=msg: self.dl_label.configure(
                    text=f"Error: {m}"))

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
