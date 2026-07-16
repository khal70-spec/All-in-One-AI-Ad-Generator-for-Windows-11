import os
import torch
import numpy as np
from PIL import Image
from config import MODELS_DIR, OUTPUTS_DIR, DEFAULT_STEPS, DEFAULT_GUIDANCE
import time


class TextToVideoGenerator:
    """Generate videos from text prompts using open source models"""

    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.pipe = None
        self.current_model = None

    def load_zeroscope(self):
        """Load ZeroScope V2 for text-to-video"""
        from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler

        model_path = os.path.join(MODELS_DIR, "zeroscope")
        if not os.path.exists(model_path):
            model_path = "cerspense/zeroscope_v2_576w"

        pipe = DiffusionPipeline.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        )
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

        if torch.cuda.is_available():
            pipe.to("cuda")
            pipe.enable_model_cpu_offload()

        self.pipe = pipe
        self.current_model = "zeroscope"
        return True

    def load_cogvideox(self):
        """Load CogVideoX for text-to-video"""
        try:
            from diffusers import CogVideoXPipeline

            model_path = os.path.join(MODELS_DIR, "cogvideox")
            if not os.path.exists(model_path):
                model_path = "THUDM/CogVideoX-2b"

            pipe = CogVideoXPipeline.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            )

            if torch.cuda.is_available():
                pipe.enable_model_cpu_offload()

            self.pipe = pipe
            self.current_model = "cogvideox"
            return True
        except Exception as e:
            print(f"CogVideoX load error: {e}")
            return False

    def generate(self, prompt, negative_prompt="", num_frames=24, width=512, height=512,
                num_steps=DEFAULT_STEPS, guidance_scale=DEFAULT_GUIDANCE,
                seed=-1, progress_callback=None, model="zeroscope"):
        """Generate video from text"""

        # Load model if needed
        if self.current_model != model or self.pipe is None:
            if progress_callback:
                progress_callback(0, f"Loading {model} model...")

            if model == "zeroscope":
                self.load_zeroscope()
            elif model == "cogvideox":
                self.load_cogvideox()

        if self.pipe is None:
            raise RuntimeError("Failed to load model")

        # Set seed
        if seed == -1:
            seed = int(time.time()) % 2**32
        generator = torch.Generator(device=self.model_manager.device).manual_seed(seed)

        if progress_callback:
            progress_callback(10, "Generating video frames...")

        try:
            # Generate
            if self.current_model == "zeroscope":
                result = self.pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_frames=num_frames,
                    width=width,
                    height=height,
                    num_inference_steps=num_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                )
                frames = result.frames[0]

            elif self.current_model == "cogvideox":
                result = self.pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_frames=num_frames,
                    num_inference_steps=num_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                )
                frames = result.frames[0]

            if progress_callback:
                progress_callback(80, "Saving video...")

            # Save video
            output_path = self._save_video(frames, seed)

            if progress_callback:
                progress_callback(100, "Complete!")

            return output_path

        except Exception as e:
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            raise

    def _save_video(self, frames, seed):
        """Save frames as video file"""
        import imageio

        timestamp = int(time.time())
        output_path = os.path.join(OUTPUTS_DIR, f"text2video_{timestamp}_{seed}.mp4")

        # Convert frames to numpy if needed
        if isinstance(frames[0], Image.Image):
            frames = [np.array(f) for f in frames]

        imageio.mimwrite(output_path, frames, fps=8, quality=8)
        return output_path
