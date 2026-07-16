import os
import json
import torch
import time
from config import MODELS_DIR, OUTPUTS_DIR, DEFAULT_STEPS, DEFAULT_GUIDANCE
from .progress import make_step_kwargs, GenerationCancelled
from .logger import get_logger
from PIL import Image

log = get_logger("t2i")


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
                 progress_callback=None, cancel_check=None):
        """Generate an image from a text prompt. Returns the output path."""

        if self.current_model != model or self.pipe is None:
            if progress_callback:
                progress_callback(0, f"Loading {model}...")
            if model == "stable_diffusion_xl":
                if self.model_manager is not None and progress_callback:
                    warn = self.model_manager.check_vram_fit(model)
                    if warn:
                        progress_callback(1, warn)
                        log.warning(warn)
                self.load_sdxl()
            else:
                raise ValueError(f"Unknown image model: {model}")

        if self.pipe is None or self.current_model != model:
            raise RuntimeError(f"Failed to load image model: {model}")

        if seed == -1:
            seed = int(time.time()) % 2**32
        device = self._device()
        generator = torch.Generator(device=device).manual_seed(seed)
        step_kwargs = make_step_kwargs(self.pipe, num_steps, progress_callback,
                                       cancel_check=cancel_check)

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
                **step_kwargs,
            )
            image = result.images[0]

            if progress_callback:
                progress_callback(80, "Saving image...")

            output_path = self._save_image(image, seed, meta={
                "type": "text_to_image",
                "model": self.current_model,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_steps": num_steps,
                "guidance_scale": guidance_scale,
                "seed": seed,
            })
            if progress_callback:
                progress_callback(100, "Complete!")
            log.info("Generated image: %s", output_path)
            return output_path
        except GenerationCancelled:
            log.info("Generation cancelled by user")
            if progress_callback:
                progress_callback(0, "Cancelled")
            raise
        except Exception as e:
            log.error("Generation failed: %s", e)
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            raise

    def _save_image(self, image: Image.Image, seed, meta=None):
        timestamp = int(time.time())
        output_path = os.path.join(OUTPUTS_DIR, f"image_{timestamp}_{seed}.png")
        image.save(output_path)
        if meta:
            try:
                meta = dict(meta)
                meta["created"] = time.strftime("%Y-%m-%d %H:%M:%S")
                with open(output_path + ".json", "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)
            except Exception as e:
                log.warning("Could not write metadata sidecar: %s", e)
        return output_path
