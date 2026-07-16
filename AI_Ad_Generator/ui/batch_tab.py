import customtkinter as ctk
from ui.styles import COLORS, FONTS
from core.batch import BatchProcessor
from config import OUTPUTS_DIR
from tkinter import filedialog
import threading
import os


class BatchTab:
    """Batch generation for multiple products / images."""

    def __init__(self, parent, model_manager, prompt_generator):
        self.parent = parent
        self.model_manager = model_manager
        self.prompt_generator = prompt_generator
        self.processor = BatchProcessor(model_manager, prompt_generator)
        self.image_list = []
        self.is_running = False
        self._create_ui()

    # ------------------------------------------------------------------ #
    def _create_ui(self):
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ============ LEFT PANEL ============
        left = ctk.CTkScrollableFrame(main_frame, width=420,
                                     fg_color=COLORS["bg_medium"], corner_radius=10)
        left.pack(side="left", fill="y", padx=(0, 10))

        ctk.CTkLabel(left, text="🔁 Batch Generator",
                     font=FONTS["heading"]).pack(pady=(10, 5))

        ctk.CTkLabel(left, text="Mode:", font=FONTS["subheading"]).pack(
            anchor="w", padx=10, pady=(10, 0))
        self.mode_var = ctk.StringVar(value="Products → Video")
        ctk.CTkOptionMenu(
            left, variable=self.mode_var,
            values=["Products → Video", "Images → Video",
                    "Generate Images", "Online Video"],
            fg_color=COLORS["entry_bg"], button_color=COLORS["accent"],
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(left, text="Online Provider:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(10, 0))
        self.provider_var = ctk.StringVar(value="pika")
        ctk.CTkOptionMenu(
            left, variable=self.provider_var,
            values=["pika", "luma"],
            fg_color=COLORS["entry_bg"], button_color=COLORS["accent"],
        ).pack(fill="x", padx=10, pady=5)

        # ---- Products ----
        ctk.CTkLabel(left, text="📦 Products (one per line):",
                     font=FONTS["subheading"]).pack(anchor="w", padx=10, pady=(15, 0))
        self.products_text = ctk.CTkTextbox(left, height=120, fg_color=COLORS["entry_bg"])
        self.products_text.pack(fill="x", padx=10, pady=5)
        self.products_text.insert("0.0", "Nike Air Max sneakers\n"
                                         "Samsung Galaxy S24\n"
                                         "Apple AirPods Pro")

        self.style_var = ctk.StringVar(value="cinematic")
        ctk.CTkOptionMenu(
            left, variable=self.style_var,
            values=list(self.prompt_generator.STYLES.keys()),
            fg_color=COLORS["entry_bg"], button_color=COLORS["accent"],
        ).pack(fill="x", padx=10, pady=5)

        self.t2v_model_var = ctk.StringVar(value="zeroscope")
        ctk.CTkOptionMenu(
            left, variable=self.t2v_model_var,
            values=["zeroscope", "cogvideox", "modelscope"],
            fg_color=COLORS["entry_bg"], button_color=COLORS["accent"],
        ).pack(fill="x", padx=10, pady=5)

        # Images
        ctk.CTkButton(
            left, text="📁 Add Images",
            fg_color=COLORS["bg_light"], hover_color=COLORS["accent"],
            command=self._add_images,
        ).pack(fill="x", padx=10, pady=(15, 5))
        self.img_list_label = ctk.CTkLabel(
            left, text="Images: 0", font=FONTS["small"],
            text_color=COLORS["text_secondary"])
        self.img_list_label.pack(padx=10)

        self.i2v_model_var = ctk.StringVar(value="svd")
        ctk.CTkOptionMenu(
            left, variable=self.i2v_model_var,
            values=["svd", "animatediff"],
            fg_color=COLORS["entry_bg"], button_color=COLORS["accent"],
        ).pack(fill="x", padx=10, pady=5)

        self.remove_bg_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(left, text="Remove Background", variable=self.remove_bg_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=20)
        self.enhance_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left, text="Enhance Image", variable=self.enhance_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=20)

        # Settings
        sframe = ctk.CTkFrame(left, fg_color="transparent")
        sframe.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(sframe, text="Steps:", font=FONTS["body"]).grid(
            row=0, column=0, sticky="w", pady=2)
        self.steps_slider = ctk.CTkSlider(sframe, from_=10, to=50, number_of_steps=40)
        self.steps_slider.set(25); self.steps_slider.grid(row=0, column=1, padx=10, sticky="ew")
        self.steps_lbl = ctk.CTkLabel(sframe, text="25", width=30)
        self.steps_lbl.grid(row=0, column=2)
        self.steps_slider.configure(command=lambda v: self.steps_lbl.configure(text=str(int(v))))

        ctk.CTkLabel(sframe, text="Guidance:", font=FONTS["body"]).grid(
            row=1, column=0, sticky="w", pady=2)
        self.guid_slider = ctk.CTkSlider(sframe, from_=1, to=20, number_of_steps=38)
        self.guid_slider.set(7.5); self.guid_slider.grid(row=1, column=1, padx=10, sticky="ew")
        self.guid_lbl = ctk.CTkLabel(sframe, text="7.5", width=30)
        self.guid_lbl.grid(row=1, column=2)
        self.guid_slider.configure(command=lambda v: self.guid_lbl.configure(text=f"{v:.1f}"))

        ctk.CTkLabel(sframe, text="Frames:", font=FONTS["body"]).grid(
            row=2, column=0, sticky="w", pady=2)
        self.frames_slider = ctk.CTkSlider(sframe, from_=8, to=48, number_of_steps=40)
        self.frames_slider.set(24); self.frames_slider.grid(row=2, column=1, padx=10, sticky="ew")
        self.frames_lbl = ctk.CTkLabel(sframe, text="24", width=30)
        self.frames_lbl.grid(row=2, column=2)
        self.frames_slider.configure(command=lambda v: self.frames_lbl.configure(text=str(int(v))))
        sframe.columnconfigure(1, weight=1)

        self.size_var = ctk.StringVar(value="512x512")
        ctk.CTkOptionMenu(
            sframe, variable=self.size_var,
            values=["256x256", "384x384", "512x512", "576x320", "320x576"],
            fg_color=COLORS["entry_bg"],
        ).grid(row=3, column=1, columnspan=2, padx=10, sticky="ew", pady=2)
        ctk.CTkLabel(sframe, text="Size:", font=FONTS["body"]).grid(
            row=3, column=0, sticky="w", pady=2)

        # Buttons
        ctk.CTkButton(
            left, text="🚀 GENERATE ALL", font=FONTS["button"], height=50,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._generate_all,
        ).pack(fill="x", padx=10, pady=15)

        self.stop_btn = ctk.CTkButton(
            left, text="⏹ Stop", fg_color=COLORS["error"],
            command=self._stop, state="disabled")
        self.stop_btn.pack(fill="x", padx=10, pady=(0, 10))

        self.progress = ctk.CTkProgressBar(left, progress_color=COLORS["accent"])
        self.progress.pack(fill="x", padx=10, pady=5)
        self.progress.set(0)
        self.status_lbl = ctk.CTkLabel(
            left, text="Ready", font=FONTS["small"],
            text_color=COLORS["text_secondary"])
        self.status_lbl.pack(padx=10, pady=(0, 10))

        # ============ RIGHT PANEL ============
        right = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        right.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(right, text="📜 Batch Log",
                     font=FONTS["heading"]).pack(pady=10)
        self.log = ctk.CTkTextbox(right, fg_color=COLORS["bg_dark"],
                                 font=("Consolas", 11), wrap="word")
        self.log.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        ctk.CTkButton(
            right, text="📂 Open Output Folder",
            fg_color=COLORS["bg_light"], command=lambda: os.startfile(OUTPUTS_DIR)
        ).pack(pady=(0, 10))

    # ------------------------------------------------------------------ #
    def _add_images(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All", "*.*")])
        self.image_list.extend(paths)
        self.img_list_label.configure(text=f"Images: {len(self.image_list)}")

    def _build_jobs(self):
        mode = self.mode_var.get()
        steps = int(self.steps_slider.get())
        guidance = float(self.guid_slider.get())
        frames = int(self.frames_slider.get())
        size = self.size_var.get().split("x")
        w, h = int(size[0]), int(size[1])
        neg = self.prompt_generator.generate_negative_prompt()

        jobs = []
        if mode == "Products → Video":
            products = [p.strip() for p in self.products_text.get("0.0", "end").splitlines() if p.strip()]
            for p in products:
                prompt = self.prompt_generator.generate_prompt(
                    p, style=self.style_var.get())
                jobs.append({
                    "type": "text", "prompt": prompt, "negative": neg,
                    "frames": frames, "width": w, "height": h,
                    "steps": steps, "guidance": guidance,
                    "model": self.t2v_model_var.get(),
                })
        elif mode == "Images → Video":
            for img in self.image_list:
                jobs.append({
                    "type": "image", "image": img,
                    "frames": frames, "motion": 127, "noise": 0.02,
                    "remove_bg": self.remove_bg_var.get(),
                    "enhance": self.enhance_var.get(),
                    "model": self.i2v_model_var.get(),
                })
        elif mode == "Generate Images":
            products = [p.strip() for p in self.products_text.get("0.0", "end").splitlines() if p.strip()]
            for p in products:
                prompt = self.prompt_generator.generate_prompt(
                    p, style=self.style_var.get(),
                    include_camera=False, include_lighting=True, include_bg=True)
                jobs.append({
                    "type": "image_gen", "prompt": prompt, "negative": neg,
                    "width": w, "height": h, "steps": steps,
                    "guidance": guidance, "model": "stable_diffusion_xl",
                })
        elif mode == "Online Video":
            products = [p.strip() for p in self.products_text.get("0.0", "end").splitlines() if p.strip()]
            for p in products:
                prompt = self.prompt_generator.generate_prompt(
                    p, style=self.style_var.get())
                jobs.append({
                    "type": "online", "prompt": prompt,
                    "provider": self.provider_var.get(),
                })
        return jobs

    def _generate_all(self):
        if self.is_running:
            return
        jobs = self._build_jobs()
        if not jobs:
            self.status_lbl.configure(text="⚠️ No jobs to run!")
            return

        self.is_running = True
        self.stop_btn.configure(state="normal")
        self.log.delete("0.0", "end")
        self.log.insert("0.0", f"Queued {len(jobs)} job(s)...\n")

        def run():
            try:
                results = self.processor.run(jobs, progress_callback=self._on_progress)
                ok = sum(1 for r in results if r["status"] == "ok")
                err = sum(1 for r in results if r["status"] == "error")
                self.parent.after(0, lambda: self._on_done(ok, err))
            except Exception as e:
                self.parent.after(0, lambda: self._on_done(0, len(jobs), str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _on_progress(self, value, message):
        self.parent.after(0, lambda: self.progress.set(value / 100))
        self.parent.after(0, lambda: self.status_lbl.configure(text=message))
        self.parent.after(0, lambda: self.log.insert("end", message + "\n"))
        self.parent.after(0, lambda: self.log.see("end"))

    def _on_done(self, ok, err, error=None):
        self.is_running = False
        self.stop_btn.configure(state="disabled")
        self.progress.set(1)
        msg = f"✅ Done! {ok} succeeded, {err} failed."
        if error:
            msg = f"❌ {error}"
        self.status_lbl.configure(text=msg)
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def _stop(self):
        self.processor.stop()
        self.status_lbl.configure(text="⏹ Stopping after current job...")
