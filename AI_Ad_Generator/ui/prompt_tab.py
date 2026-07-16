import customtkinter as ctk
from ui.styles import COLORS, FONTS
from config import AD_TEMPLATES


class PromptTab:
    """AI Prompt Generator tab"""

    def __init__(self, parent, prompt_generator):
        self.parent = parent
        self.prompt_generator = prompt_generator
        self._create_ui()

    def _create_ui(self):
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ============ LEFT PANEL ============
        left_panel = ctk.CTkFrame(main_frame, width=400,
                                 fg_color=COLORS["bg_medium"], corner_radius=10)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        ctk.CTkLabel(left_panel, text="💡 Prompt Generator",
                     font=FONTS["heading"]).pack(pady=(15, 10))

        # Product Name
        ctk.CTkLabel(left_panel, text="Product Name:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=15, pady=(10, 0))

        self.product_entry = ctk.CTkEntry(
            left_panel,
            placeholder_text="e.g., Samsung Galaxy S24",
            fg_color=COLORS["entry_bg"],
            height=35,
        )
        self.product_entry.pack(fill="x", padx=15, pady=5)

        # Custom Details
        ctk.CTkLabel(left_panel, text="Custom Details (optional):",
                     font=FONTS["subheading"]).pack(anchor="w", padx=15, pady=(10, 0))

        self.details_entry = ctk.CTkEntry(
            left_panel,
            placeholder_text="e.g., black color, on wooden table",
            fg_color=COLORS["entry_bg"],
            height=35,
        )
        self.details_entry.pack(fill="x", padx=15, pady=5)

        # Style Selection
        ctk.CTkLabel(left_panel, text="Ad Style:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=15, pady=(10, 0))

        styles = list(self.prompt_generator.STYLES.keys())
        self.style_var = ctk.StringVar(value="cinematic")
        style_menu = ctk.CTkOptionMenu(
            left_panel,
            variable=self.style_var,
            values=styles,
            fg_color=COLORS["entry_bg"],
            button_color=COLORS["accent"],
        )
        style_menu.pack(fill="x", padx=15, pady=5)

        # Options
        ctk.CTkLabel(left_panel, text="Include:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=15, pady=(10, 0))

        self.camera_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_panel, text="Camera Movement",
                       variable=self.camera_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=25, pady=2)

        self.lighting_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_panel, text="Lighting Details",
                       variable=self.lighting_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=25, pady=2)

        self.bg_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_panel, text="Background Description",
                       variable=self.bg_var,
                       fg_color=COLORS["accent"]).pack(anchor="w", padx=25, pady=2)

        # Number of variations
        ctk.CTkLabel(left_panel, text="Variations:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=15, pady=(10, 0))

        self.variations_slider = ctk.CTkSlider(left_panel, from_=1, to=10, number_of_steps=9)
        self.variations_slider.set(5)
        self.variations_slider.pack(fill="x", padx=15, pady=5)

        # Generate Button
        ctk.CTkButton(
            left_panel,
            text="🤖 Generate Prompts",
            font=FONTS["button"],
            height=50,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._generate_single,
        ).pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(
            left_panel,
            text="📋 Generate Multiple Variations",
            font=FONTS["button"],
            height=40,
            fg_color=COLORS["bg_light"],
            hover_color=COLORS["accent"],
            command=self._generate_batch,
        ).pack(fill="x", padx=15, pady=5)

        # Template buttons
        ctk.CTkLabel(left_panel, text="Quick Templates:",
                     font=FONTS["subheading"]).pack(anchor="w", padx=15, pady=(15, 5))

        for key, template in AD_TEMPLATES.items():
            ctk.CTkButton(
                left_panel,
                text=f"📌 {template['name']}",
                height=30,
                fg_color=COLORS["entry_bg"],
                hover_color=COLORS["accent"],
                command=lambda t=template: self._use_template(t),
            ).pack(fill="x", padx=15, pady=2)

        # ============ RIGHT PANEL - OUTPUT ============
        right_panel = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_medium"],
                                  corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)

        header_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(header_frame, text="📝 Generated Prompts",
                     font=FONTS["heading"]).pack(side="left")

        ctk.CTkButton(header_frame, text="📋 Copy All",
                      width=100, fg_color=COLORS["bg_light"],
                      command=self._copy_all).pack(side="right")

        self.output_text = ctk.CTkTextbox(
            right_panel,
            fg_color=COLORS["bg_dark"],
            font=("Consolas", 12),
            wrap="word",
        )
        self.output_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Default content
        self.output_text.insert("0.0",
            "Welcome to the AI Prompt Generator!\n\n"
            "1. Enter your product name\n"
            "2. Choose a style\n"
            "3. Click 'Generate Prompts'\n\n"
            "The generated prompts are optimized for:\n"
            "• Stable Video Diffusion\n"
            "• AnimateDiff\n"
            "• ZeroScope\n"
            "• CogVideoX\n"
            "• And other AI video models\n"
        )

    def _generate_single(self):
        product = self.product_entry.get() or "product"
        details = self.details_entry.get()
        style = self.style_var.get()

        prompt = self.prompt_generator.generate_prompt(
            product_name=product,
            style=style,
            custom_details=details,
            include_camera=self.camera_var.get(),
            include_lighting=self.lighting_var.get(),
            include_bg=self.bg_var.get(),
        )

        negative = self.prompt_generator.generate_negative_prompt()

        self.output_text.delete("0.0", "end")
        self.output_text.insert("0.0",
            f"═══════════════════════════════════════\n"
            f"  GENERATED PROMPT ({style.upper()} STYLE)\n"
            f"═══════════════════════════════════════\n\n"
            f"📝 PROMPT:\n{prompt}\n\n"
            f"🚫 NEGATIVE PROMPT:\n{negative}\n\n"
            f"═══════════════════════════════════════\n"
            f"  RECOMMENDED SETTINGS\n"
            f"═══════════════════════════════════════\n\n"
            f"Steps: 25-30\n"
            f"Guidance: 7.5\n"
            f"Size: 512x512\n"
            f"Frames: 24\n"
        )

    def _generate_batch(self):
        product = self.product_entry.get() or "product"
        details = self.details_entry.get()
        count = int(self.variations_slider.get())

        prompts = self.prompt_generator.generate_batch_prompts(
            product_name=product,
            count=count,
            custom_details=details,
        )

        self.output_text.delete("0.0", "end")
        self.output_text.insert("0.0",
            f"═══════════════════════════════════════\n"
            f"  {count} PROMPT VARIATIONS\n"
            f"  Product: {product}\n"
            f"═══════════════════════════════════════\n\n"
        )

        for i, p in enumerate(prompts, 1):
            self.output_text.insert("end",
                f"──── Variation {i} ({p['style'].upper()}) ────\n\n"
                f"📝 PROMPT:\n{p['prompt']}\n\n"
                f"🚫 NEGATIVE:\n{p['negative']}\n\n\n"
            )

    def _use_template(self, template):
        product = self.product_entry.get() or "product"
        prompt = template["prompt_template"].format(product=product)

        self.output_text.delete("0.0", "end")
        self.output_text.insert("0.0",
            f"═══════════════════════════════════════\n"
            f"  TEMPLATE: {template['name']}\n"
            f"═══════════════════════════════════════\n\n"
            f"📝 PROMPT:\n{prompt}\n\n"
            f"🚫 NEGATIVE:\n{template['negative']}\n\n"
            f"⚙️ SETTINGS:\n"
            f"Steps: {template['steps']}\n"
            f"Guidance: {template['guidance']}\n"
        )

    def _copy_all(self):
        content = self.output_text.get("0.0", "end")
        self.parent.clipboard_clear()
        self.parent.clipboard_append(content)
