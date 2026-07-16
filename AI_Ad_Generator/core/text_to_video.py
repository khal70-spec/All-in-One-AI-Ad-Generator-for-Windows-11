import os
import json
import torch
import numpy as np
from PIL import Image
from typing import Optional, Callable, Dict, Any
from config import MODELS_DIR, OUTPUTS_DIR, DEFAULT_STEPS, DEFAULT_GUIDANCE
from .progress import make_step_kwargs, GenerationCancelled
from .logger import get_logger
import time

log = get_logger("t2v")


class TextToVideoGenerator:
    """Generate videos from text prompts using open source models.
    
    Supports ZeroScope, CogVideoX, ModelScope, Mochi, HunyuanVideo, and LTX-Video.
    Includes automatic VRAM management, error recovery, and progress tracking.
    """

    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.pipe = None
        self.current_model = None

    def _validate_inputs(self, prompt: str, negative_prompt: str = "", width: int = 512, 
                        height: int = 512, num_frames: int = 24) -> None:
        """Validate generation inputs.
        
        Args:
            prompt: Text prompt for generation
            negative_prompt: Negative prompt to avoid
            width: Video width in pixels
            height: Video height in pixels
            num_frames: Number of frames to generate
            
        Raises:
            ValueError: If inputs are invalid
        """
        if not prompt or not isinstance(prompt, str) or len(prompt.strip()) == 0:
            raise ValueError("Prompt cannot be empty")
        if len(prompt) > 1000:
            raise ValueError("Prompt too long (max 1000 characters)")
        if width < 256 or height < 256:
            raise ValueError("Video dimensions must be at least 256x256")
        if width > 1024 or height > 1024:
            raise ValueError("Video dimensions cannot exceed 1024x1024")
        if num_frames < 1 or num_frames > 256:
            raise ValueError("Number of frames must be between 1 and 256")

    def load_zeroscope(self) -> bool:
        """Load ZeroScope V2 for text-to-video.
        
        Returns:
            True if load successful, False otherwise
        """
        try:
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
                pipe.enable_model_cpu_offload()

            self.pipe = pipe
            self.current_model = "zeroscope"
            return True
        except Exception as e:
            log.error("ZeroScope load error: %s", e)
            return False

    def load_modelscope(self) -> bool:
        """Load ModelScope text-to-video (damo-vilab/text-to-video-ms-1.7b).
        
        Returns:
            True if load successful, False otherwise
        """
        try:
            from diffusers import TextToVideoSDPipeline

            model_path = os.path.join(MODELS_DIR, "modelscope")
            if not os.path.exists(model_path):
                model_path = "damo-vilab/text-to-video-ms-1.7b"

            pipe = TextToVideoSDPipeline.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            )

            if torch.cuda.is_available():
                pipe.enable_model_cpu_offload()

            self.pipe = pipe
            self.current_model = "modelscope"
            return True
        except Exception as e:
            log.error("ModelScope load error: %s", e)
            return False

    def load_cogvideox(self) -> bool:
        """Load CogVideoX for text-to-video.
        
        Returns:
            True if load successful, False otherwise
        """
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
            log.error("CogVideoX load error: %s", e)
            return False

    def load_mochi(self) -> bool:
        """Load Mochi 1 (genmo/mochi-1-preview) text-to-video.
        
        Returns:
            True if load successful, False otherwise
        """
        try:
            from diffusers import MochiPipeline

            model_path = os.path.join(MODELS_DIR, "mochi")
            if not os.path.exists(model_path):
                model_path = "genmo/mochi-1-preview"

            pipe = MochiPipeline.from_pretrained(
                model_path, variant="bf16", torch_dtype=torch.bfloat16)
            if torch.cuda.is_available():
                pipe.enable_model_cpu_offload()
            self.pipe = pipe
            self.current_model = "mochi"
            return True
        except Exception as e:
            log.error("Mochi load error: %s", e)
            return False

    def load_hunyuanvideo(self) -> bool:
        """Load HunyuanVideo (tencent/HunyuanVideo) text-to-video.
        
        Returns:
            True if load successful, False otherwise
        """
        try:
            from diffusers import HunyuanVideoPipeline

            model_path = os.path.join(MODELS_DIR, "hunyuanvideo")
            if not os.path.exists(model_path):
                model_path = "tencent/HunyuanVideo"

            pipe = HunyuanVideoPipeline.from_pretrained(
                model_path, torch_dtype=torch.float16)
            if torch.cuda.is_available():
                pipe.enable_model_cpu_offload()
            self.pipe = pipe
            self.current_model = "hunyuanvideo"
            return True
        except Exception as e:
            log.error("HunyuanVideo load error: %s", e)
            return False

    def load_ltx(self) -> bool:
        """Load LTX-Video (Lightricks/LTX-Video) text-to-video.
        
        Returns:
            True if load successful, False otherwise
        """
        try:
            from diffusers import LTXVideoPipeline

            model_path = os.path.join(MODELS_DIR, "ltx_video")
            if not os.path.exists(model_path):
                model_path = "Lightricks/LTX-Video"

            pipe = LTXVideoPipeline.from_pretrained(
                model_path, torch_dtype=torch.bfloat16)
            if torch.cuda.is_available():
                pipe.enable_model_cpu_offload()
            self.pipe = pipe
            self.current_model = "ltx_video"
            return True
        except Exception as e:
            log.error("LTX-Video load error: %s", e)
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

    def generate(self, prompt: str, negative_prompt: str = "", num_frames: int = 24, 
                width: int = 512, height: int = 512, num_steps: int = DEFAULT_STEPS, 
                guidance_scale: float = DEFAULT_GUIDANCE, seed: int = -1, 
                progress_callback: Optional[Callable] = None, model: str = "zeroscope",
                cancel_check: Optional[Callable] = None) -> str:
        """Generate video from text.
        
        Args:
            prompt: Text description of the video
            negative_prompt: Things to avoid in the video
            num_frames: Number of frames to generate
            width: Video width in pixels
            height: Video height in pixels
            num_steps: Number of diffusion steps
            guidance_scale: How closely to follow the prompt
            seed: Random seed (-1 for random)
            progress_callback: Callback for progress updates
            model: Model name to use
            cancel_check: Callback to check if generation should be cancelled
            
        Returns:
            Path to generated video file
            
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If model load fails
            GenerationCancelled: If generation is cancelled by user
        """
        # Validate inputs
        self._validate_inputs(prompt, negative_prompt, width, height, num_frames)

        # Load model if needed
        if self.current_model != model or self.pipe is None:
            if progress_callback:
                progress_callback(0, f"Loading {model} model...")
            warn = self.model_manager.check_vram_fit(model)
            if warn and progress_callback:
                progress_callback(1, warn)
                log.warning(warn)

            if model == "zeroscope":
                success = self.load_zeroscope()
            elif model == "cogvideox":
                success = self.load_cogvideox()
            elif model == "modelscope":
                success = self.load_modelscope()
            elif model == "mochi":
                success = self.load_mochi()
            elif model == "hunyuanvideo":
                success = self.load_hunyuanvideo()
            elif model == "ltx_video":
                success = self.load_ltx()
            else:
                raise ValueError(f"Unknown text-to-video model: {model}")
            
            if not success:
                raise RuntimeError(f"Failed to load model: {model}")

        # Guard against a failed load
        if self.pipe is None or self.current_model != model:
            raise RuntimeError(f"Failed to load model: {model}")

        # Set seed
        if seed == -1:
            seed = int(time.time()) % 2**32
        generator = torch.Generator(device=self.model_manager.device).manual_seed(seed)
        step_kwargs = make_step_kwargs(self.pipe, num_steps, progress_callback,
                                       cancel_check=cancel_check)

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
                    **step_kwargs,
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
                    **step_kwargs,
                )
                frames = result.frames[0]

            elif self.current_model == "modelscope":
                # ModelScope T2V does not take a negative prompt and is trained
                # at 256x256, so we pin the resolution to keep memory/shape safe.
                result = self.pipe(
                    prompt=prompt,
                    num_frames=min(num_frames, 16),
                    height=256,
                    width=256,
                    num_inference_steps=num_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                    **step_kwargs,
                )
                frames = result.frames[0]

            elif self.current_model == "mochi":
                # Mochi is trained at 768x480 and prefers bf16.
                result = self.pipe(
                    prompt=prompt,
                    num_frames=min(num_frames, 84),
                    height=480,
                    width=768,
                    num_inference_steps=num_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                    **step_kwargs,
                )
                frames = result.frames[0]

            elif self.current_model == "hunyuanvideo":
                # HunyuanVideo expects height/width multiples of 16.
                result = self.pipe(
                    prompt=prompt,
                    num_frames=min(num_frames, 30),
                    height=512,
                    width=512,
                    num_inference_steps=num_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                    **step_kwargs,
                )
                frames = result.frames[0]

            elif self.current_model == "ltx_video":
                # LTX-Video needs height/width multiples of 32 and
                # num_frames = 8*k + 1.
                h, w = 512, 768
                nf = 8 * max(int(num_frames // 8), 1) + 1
                result = self.pipe(
                    prompt=prompt,
                    num_frames=nf,
                    height=h,
                    width=w,
                    num_inference_steps=num_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                    **step_kwargs,
                )
                frames = result.frames[0]

            if progress_callback:
                progress_callback(80, "Saving video...")

            # Save video (+ metadata sidecar for reproducibility)
            output_path = self._save_video(frames, seed, meta={
                "type": "text_to_video",
                "model": self.current_model,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "num_frames": num_frames,
                "width": width,
                "height": height,
                "num_steps": num_steps,
                "guidance_scale": guidance_scale,
                "seed": seed,
            })

            if progress_callback:
                progress_callback(100, "Complete!")

            log.info("Generated text-to-video: %s", output_path)
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
        """Save frames as video file (+ optional JSON metadata sidecar).
        
        Args:
            frames: List of PIL Images or numpy arrays
            seed: Seed used for generation
            meta: Metadata dictionary to save alongside video
            
        Returns:
            Path to saved video file
        """
        import imageio

        timestamp = int(time.time())
        output_path = os.path.join(OUTPUTS_DIR, f"text2video_{timestamp}_{seed}.mp4")

        try:
            # Convert frames to numpy if needed
            if isinstance(frames[0], Image.Image):
                frames = [np.array(f) for f in frames]

            imageio.mimwrite(output_path, frames, fps=8, quality=8)
            self._write_sidecar(output_path, meta)
            return output_path
        except Exception as e:
            log.error("Failed to save video: %s", e)
            raise

    @staticmethod
    def _write_sidecar(media_path: str, meta: Optional[Dict[str, Any]]) -> None:
        """Write ``<media>.json`` holding the generation parameters.
        
        Args:
            media_path: Path to media file
            meta: Metadata dictionary to save
        """
        if not meta:
            return
        try:
            meta = dict(meta)
            meta["created"] = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(media_path + ".json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.warning("Could not write metadata sidecar: %s", e)
