import random


class PromptGenerator:
    """Generates optimized prompts for product advertisements"""

    STYLES = {
        "cinematic": "cinematic lighting, professional photography, 4K, ultra detailed",
        "minimal": "minimalist, clean background, modern, simple elegant",
        "luxury": "luxury, premium, dark background, golden accents, dramatic lighting",
        "vibrant": "vibrant colors, energetic, dynamic, eye-catching",
        "natural": "natural lighting, organic, warm tones, lifestyle photography",
        "tech": "futuristic, tech, neon glow, modern, sleek design",
        "vintage": "vintage, retro, warm film grain, nostalgic",
        "studio": "studio photography, white background, professional lighting, commercial",
    }

    CAMERA_MOVES = [
        "slow zoom in",
        "rotating 360 view",
        "dolly shot",
        "pan left to right",
        "tilt up reveal",
        "tracking shot",
        "static close-up",
        "pull back reveal",
    ]

    LIGHTING = [
        "studio lighting",
        "golden hour lighting",
        "dramatic side lighting",
        "soft diffused lighting",
        "rim lighting",
        "neon lighting",
        "natural sunlight",
        "moody dark lighting",
    ]

    BACKGROUNDS = [
        "clean white background",
        "dark elegant background",
        "gradient background",
        "blurred lifestyle background",
        "marble surface",
        "wooden table",
        "abstract geometric background",
        "nature background",
    ]

    def generate_prompt(self, product_name, style="cinematic", custom_details="",
                       include_camera=True, include_lighting=True, include_bg=True):
        """Generate a comprehensive ad prompt"""

        parts = []

        # Main subject
        parts.append(f"Professional product advertisement for {product_name}")

        # Custom details
        if custom_details:
            parts.append(custom_details)

        # Style
        if style in self.STYLES:
            parts.append(self.STYLES[style])

        # Background
        if include_bg:
            parts.append(random.choice(self.BACKGROUNDS))

        # Lighting
        if include_lighting:
            parts.append(random.choice(self.LIGHTING))

        # Camera movement (for video)
        if include_camera:
            parts.append(random.choice(self.CAMERA_MOVES))

        # Quality boosters
        parts.append("high quality, detailed, sharp focus, commercial advertisement")

        prompt = ", ".join(parts)
        return prompt

    def generate_negative_prompt(self):
        """Generate negative prompt for better quality"""
        negatives = [
            "blurry", "low quality", "distorted", "ugly", "bad anatomy",
            "watermark", "text", "logo", "signature", "cropped",
            "out of frame", "deformed", "disfigured", "bad proportions",
            "duplicate", "error", "extra fingers", "gross proportions",
            "mutation", "poorly drawn", "worst quality", "jpeg artifacts",
        ]
        return ", ".join(negatives)

    def generate_batch_prompts(self, product_name, count=5, custom_details=""):
        """Generate multiple prompt variations"""
        prompts = []
        styles = list(self.STYLES.keys())

        for i in range(count):
            style = styles[i % len(styles)]
            prompt = self.generate_prompt(
                product_name=product_name,
                style=style,
                custom_details=custom_details,
            )
            prompts.append({
                "style": style,
                "prompt": prompt,
                "negative": self.generate_negative_prompt(),
            })

        return prompts

    def enhance_prompt(self, basic_prompt):
        """Enhance a basic prompt with quality boosters"""
        enhancers = [
            "masterpiece", "best quality", "ultra detailed",
            "professional", "4K resolution", "sharp focus",
            "commercial photography", "award winning",
        ]
        enhanced = basic_prompt + ", " + ", ".join(random.sample(enhancers, 4))
        return enhanced
