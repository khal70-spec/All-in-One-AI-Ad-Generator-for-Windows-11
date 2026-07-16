import os
import torch
import time
from config import MODELS_DIR, OUTPUTS_DIR, DEFAULT_STEPS, DEFAULT_GUIDANCE
from PIL import Image


class TextToImageGenerator:
    """Generate product images from text using Stable Diffusion XL."""

    def __init__(self, model_manager=None):
        self.model_manager = model_manager
        self.pipe = None
        self.current_model = None

    def _device(self):
        if self.model_manager is not None:
            return self.model_manager.device
        return "cuda" if torch.cuda.is_available() else "cpu"

    def load_sdxl(self):
        """Load Stable Diffusion XL for text-to-image."""
        from diffusers import StableDiffusionXLPipeline

        model_path = os.path.join(MODELS_DIR, "stable_diffusion_xl")
        if not os.path.exists(model_path):
            model_path = "stabilityai/stable-diffusion-xl-base-1.0"

        pipe = StableDiffusionXLPipeline.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        )

        if torch.cuda.is_available():
            pipe.enable_model_cpu_offload()
        else:
            pipe = pipe.to("cpu")

        self.pipe = pipe
        self.current_model = "stable_diffusion_xl"
        return True

    def generate(self, prompt, negative_prompt="", width=1024, height=1024,
                 num_steps=DEFAULT_STEPS, guidance_scale=DEFAULT_GUIDANCE,
                 seed=-1, model="stable_diffusion_xl",
                 progress_callback=None):
        """Generate an image from a text prompt. Returns the output path."""

        if self.current_model != model or self.pipe is None:
            if progress_callback:
                progress_callback(0, f"Loading {model}...")
            if model == "stable_diffusion_xl":
                self.load_sdxl()
            else:
                raise ValueError(f"Unknown image model: {model}")

        if self.pipe is None:
            raise RuntimeError("Failed to load image model")

        if seed == -1:
            seed = int(time.time()) % 2**32
        device = self._device()
        generator = torch.Generator(device=device).manual_seed(seed)

        if progress_callback:
            progress_callback(10, "Generating image...")

        try:
            result = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=num_steps,
                guidance_scale=guidance_scale,
                generator=generator,
            )
            image = result.images[0]

            if progress_callback:
                progress_callback(80, "Saving image...")

            output_path = self._save_image(image, seed)
            if progress_callback:
                progress_callback(100, "Complete!")
            return output_path
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            raise

    def _save_image(self, image: Image.Image, seed):
        timestamp = int(time.time())
        output_path = os.path.join(OUTPUTS_DIR, f"image_{timestamp}_{seed}.png")
        image.save(output_path)
        return output_path
