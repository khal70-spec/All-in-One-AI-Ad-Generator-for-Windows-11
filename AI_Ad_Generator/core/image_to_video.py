import os
import torch
import numpy as np
from PIL import Image
from config import MODELS_DIR, OUTPUTS_DIR
from .progress import make_step_kwargs
import time


class ImageToVideoGenerator:
    """Generate videos from images using open source models"""

    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.pipe = None
        self.current_model = None

    def load_svd(self):
        """Load Stable Video Diffusion"""
        from diffusers import StableVideoDiffusionPipeline

        model_path = os.path.join(MODELS_DIR, "stable_video_diffusion")
        if not os.path.exists(model_path):
            model_path = "stabilityai/stable-video-diffusion-img2vid-xt"

        pipe = StableVideoDiffusionPipeline.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            variant="fp16" if torch.cuda.is_available() else None,
        )

        if torch.cuda.is_available():
            pipe.enable_model_cpu_offload()

        self.pipe = pipe
        self.current_model = "svd"
        return True

    def load_animatediff(self):
        """Load AnimateDiff"""
        try:
            from diffusers import AnimateDiffPipeline, MotionAdapter, DDIMScheduler

            adapter = MotionAdapter.from_pretrained(
                "guoyww/animatediff-motion-adapter-v1-5-3",
                torch_dtype=torch.float16,
            )

            pipe = AnimateDiffPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                motion_adapter=adapter,
                torch_dtype=torch.float16,
            )
            pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)

            if torch.cuda.is_available():
                pipe.enable_model_cpu_offload()

            self.pipe = pipe
            self.current_model = "animatediff"
            return True
        except Exception as e:
            print(f"AnimateDiff load error: {e}")
            return False

    def generate_from_image(self, image_path, num_frames=25, fps=7,
                           motion_bucket_id=127, noise_aug=0.02, num_steps=25,
                           seed=-1, progress_callback=None, model="svd"):
        """Generate video from a single image"""

        # Load model
        if self.current_model != model or self.pipe is None:
            if progress_callback:
                progress_callback(0, f"Loading {model} model...")

            if model == "svd":
                self.load_svd()
            elif model == "animatediff":
                self.load_animatediff()
            else:
                raise ValueError(f"Unknown image-to-video model: {model}")

        # Guard against a failed load (load_* returns False on error) so we
        # never silently animate with a previously loaded, different model.
        if self.pipe is None or self.current_model != model:
            raise RuntimeError(f"Failed to load model: {model}")

        # Prepare image
        if progress_callback:
            progress_callback(10, "Preparing image...")

        image = Image.open(image_path).convert("RGB")
        image = image.resize((512, 512), Image.LANCZOS)

        # Set seed
        if seed == -1:
            seed = int(time.time()) % 2**32
        generator = torch.Generator(device="cpu").manual_seed(seed)
        step_kwargs = make_step_kwargs(self.pipe, num_steps, progress_callback)

        if progress_callback:
            progress_callback(20, "Generating video...")

        try:
            if self.current_model == "svd":
                result = self.pipe(
                    image=image,
                    num_frames=num_frames,
                    num_inference_steps=num_steps,
                    decode_chunk_size=8,
                    motion_bucket_id=motion_bucket_id,
                    noise_aug_strength=noise_aug,
                    generator=generator,
                    **step_kwargs,
                )
                frames = result.frames[0]

            elif self.current_model == "animatediff":
                result = self.pipe(
                    prompt="product advertisement, smooth motion, professional",
                    num_frames=num_frames,
                    num_inference_steps=num_steps,
                    generator=generator,
                    **step_kwargs,
                )
                frames = result.frames[0]

            if progress_callback:
                progress_callback(80, "Saving video...")

            output_path = self._save_video(frames, seed)

            if progress_callback:
                progress_callback(100, "Complete!")

            return output_path

        except Exception as e:
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            raise

    def _save_video(self, frames, seed):
        """Save frames as video"""
        import imageio

        timestamp = int(time.time())
        output_path = os.path.join(OUTPUTS_DIR, f"img2video_{timestamp}_{seed}.mp4")

        if isinstance(frames[0], Image.Image):
            frames = [np.array(f) for f in frames]

        imageio.mimwrite(output_path, frames, fps=8, quality=8)
        return output_path
