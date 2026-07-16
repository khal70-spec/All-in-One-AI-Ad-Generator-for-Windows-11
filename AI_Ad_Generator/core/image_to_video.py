import os
import json
import torch
import numpy as np
from PIL import Image
from typing import Optional, Callable, Dict, Any
from config import MODELS_DIR, OUTPUTS_DIR
from .progress import make_step_kwargs, GenerationCancelled
from .logger import get_logger
import time

log = get_logger("i2v")

# UI model key -> config.MODELS key (for VRAM fit checks)
_MODEL_KEY_MAP = {"svd": "stable_video_diffusion", "animatediff": "animatediff"}


class ImageToVideoGenerator:
    """Generate videos from images using open source models.
    
    Supports Stable Video Diffusion and AnimateDiff with automatic VRAM management,
    error recovery, and progress tracking.
    """

    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.pipe = None
        self.current_model = None

    def _validate_image_path(self, image_path: str) -> None:
        """Validate that image path exists and is readable.
        
        Args:
            image_path: Path to image file
            
        Raises:
            FileNotFoundError: If image doesn't exist
            IOError: If image can't be read
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        if not os.path.isfile(image_path):
            raise IOError(f"Path is not a file: {image_path}")
        if not os.access(image_path, os.R_OK):
            raise IOError(f"Image file is not readable: {image_path}")

    def _validate_inputs(self, num_frames: int = 25, num_steps: int = 25) -> None:
        """Validate generation parameters.
        
        Args:
            num_frames: Number of frames to generate
            num_steps: Number of diffusion steps
            
        Raises:
            ValueError: If inputs are invalid
        """
        if num_frames < 1 or num_frames > 256:
            raise ValueError("Number of frames must be between 1 and 256")
        if num_steps < 1 or num_steps > 100:
            raise ValueError("Number of steps must be between 1 and 100")

    def load_svd(self) -> bool:
        """Load Stable Video Diffusion.
        
        Returns:
            True if load successful, False otherwise
        """
        try:
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
        except Exception as e:
            log.error("SVD load error: %s", e)
            return False

    def load_animatediff(self) -> bool:
        """Load AnimateDiff.
        
        Returns:
            True if load successful, False otherwise
        """
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
            log.error("AnimateDiff load error: %s", e)
            return False

    def unload_model(self) -> None:
        """Unload current model and free VRAM."""
        try:
            if self.pipe is not None:
                del self.pipe
                self.pipe = None
                self.current_model = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
        except Exception as e:
            log.warning("Error unloading model: %s", e)

    def generate_from_image(self, image_path: str, num_frames: int = 25, fps: int = 7,
                           motion_bucket_id: int = 127, noise_aug: float = 0.02, 
                           num_steps: int = 25, seed: int = -1, 
                           progress_callback: Optional[Callable] = None, 
                           model: str = "svd", cancel_check: Optional[Callable] = None) -> str:
        """Generate video from a single image.
        
        Args:
            image_path: Path to input image
            num_frames: Number of frames to generate
            fps: Frames per second
            motion_bucket_id: Motion control parameter
            noise_aug: Noise augmentation strength
            num_steps: Number of diffusion steps
            seed: Random seed (-1 for random)
            progress_callback: Callback for progress updates
            model: Model name to use
            cancel_check: Callback to check if generation should be cancelled
            
        Returns:
            Path to generated video file
            
        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If inputs are invalid
            RuntimeError: If model load fails
            GenerationCancelled: If generation is cancelled by user
        """
        # Validate image exists
        self._validate_image_path(image_path)
        
        # Validate parameters
        self._validate_inputs(num_frames, num_steps)

        # Load model
        if self.current_model != model or self.pipe is None:
            if progress_callback:
                progress_callback(0, f"Loading {model} model...")
            warn = self.model_manager.check_vram_fit(_MODEL_KEY_MAP.get(model, model))
            if warn and progress_callback:
                progress_callback(1, warn)
                log.warning(warn)

            if model == "svd":
                success = self.load_svd()
            elif model == "animatediff":
                success = self.load_animatediff()
            else:
                raise ValueError(f"Unknown image-to-video model: {model}")
            
            if not success:
                raise RuntimeError(f"Failed to load model: {model}")

        # Guard against a failed load
        if self.pipe is None or self.current_model != model:
            raise RuntimeError(f"Failed to load model: {model}")

        # Prepare image
        if progress_callback:
            progress_callback(10, "Preparing image...")

        try:
            image = Image.open(image_path).convert("RGB")
            image = image.resize((512, 512), Image.LANCZOS)
        except Exception as e:
            log.error("Failed to load/process image: %s", e)
            raise IOError(f"Failed to load image: {str(e)}")

        # Set seed
        if seed == -1:
            seed = int(time.time()) % 2**32
        generator = torch.Generator(device="cpu").manual_seed(seed)
        step_kwargs = make_step_kwargs(self.pipe, num_steps, progress_callback,
                                       cancel_check=cancel_check)

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

            output_path = self._save_video(frames, seed, meta={
                "type": "image_to_video",
                "model": self.current_model,
                "source_image": os.path.basename(image_path),
                "num_frames": num_frames,
                "num_steps": num_steps,
                "motion_bucket_id": motion_bucket_id,
                "noise_aug": noise_aug,
                "seed": seed,
            })

            if progress_callback:
                progress_callback(100, "Complete!")

            log.info("Generated image-to-video: %s", output_path)
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

    def _save_video(self, frames, seed: int, meta: Optional[Dict[str, Any]] = None) -> str:
        """Save frames as video (+ optional JSON metadata sidecar).
        
        Args:
            frames: List of PIL Images or numpy arrays
            seed: Seed used for generation
            meta: Metadata dictionary to save alongside video
            
        Returns:
            Path to saved video file
        """
        import imageio

        timestamp = int(time.time())
        output_path = os.path.join(OUTPUTS_DIR, f"img2video_{timestamp}_{seed}.mp4")

        try:
            if isinstance(frames[0], Image.Image):
                frames = [np.array(f) for f in frames]

            imageio.mimwrite(output_path, frames, fps=8, quality=8)
            if meta:
                try:
                    meta = dict(meta)
                    meta["created"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    with open(output_path + ".json", "w", encoding="utf-8") as f:
                        json.dump(meta, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    log.warning("Could not write metadata sidecar: %s", e)
            return output_path
        except Exception as e:
            log.error("Failed to save video: %s", e)
            raise
