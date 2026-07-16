import os
import json
import torch
import numpy as np
from PIL import Image
from config import MODELS_DIR, OUTPUTS_DIR, DEFAULT_STEPS, DEFAULT_GUIDANCE
from .progress import make_step_kwargs, GenerationCancelled
from .logger import get_logger
import time

log = get_logger("t2v")


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
            # CPU offload already handles moving weights to the GPU on demand;
            # calling pipe.to("cuda") first defeats its purpose.
            pipe.enable_model_cpu_offload()

        self.pipe = pipe
        self.current_model = "zeroscope"
        return True

    def load_modelscope(self):
        """Load ModelScope text-to-video (damo-vilab/text-to-video-ms-1.7b)"""
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
            log.error("CogVideoX load error: %s", e)
            return False

    def load_mochi(self):
        """Load Mochi 1 (genmo/mochi-1-preview) text-to-video."""
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

    def load_hunyuanvideo(self):
        """Load HunyuanVideo (tencent/HunyuanVideo) text-to-video."""
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

    def load_ltx(self):
        """Load LTX-Video (Lightricks/LTX-Video) text-to-video."""
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

    def generate(self, prompt, negative_prompt="", num_frames=24, width=512, height=512,
                num_steps=DEFAULT_STEPS, guidance_scale=DEFAULT_GUIDANCE,
                seed=-1, progress_callback=None, model="zeroscope",
                cancel_check=None):
        """Generate video from text"""

        # Load model if needed
        if self.current_model != model or self.pipe is None:
            if progress_callback:
                progress_callback(0, f"Loading {model} model...")
            warn = self.model_manager.check_vram_fit(model)
            if warn and progress_callback:
                progress_callback(1, warn)
                log.warning(warn)

            if model == "zeroscope":
                self.load_zeroscope()
            elif model == "cogvideox":
                self.load_cogvideox()
            elif model == "modelscope":
                self.load_modelscope()
            elif model == "mochi":
                self.load_mochi()
            elif model == "hunyuanvideo":
                self.load_hunyuanvideo()
            elif model == "ltx_video":
                self.load_ltx()
            else:
                raise ValueError(f"Unknown text-to-video model: {model}")

        # Guard against a failed load (load_* returns False on error, or an
        # unknown model) so we never silently generate with a previously
        # loaded, different model.
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

    def _save_video(self, frames, seed, meta=None):
        """Save frames as video file (+ optional JSON metadata sidecar)."""
        import imageio

        timestamp = int(time.time())
        output_path = os.path.join(OUTPUTS_DIR, f"text2video_{timestamp}_{seed}.mp4")

        # Convert frames to numpy if needed
        if isinstance(frames[0], Image.Image):
            frames = [np.array(f) for f in frames]

        imageio.mimwrite(output_path, frames, fps=8, quality=8)
        self._write_sidecar(output_path, meta)
        return output_path

    @staticmethod
    def _write_sidecar(media_path, meta):
        """Write ``<media>.json`` holding the generation parameters."""
        if not meta:
            return
        try:
            meta = dict(meta)
            meta["created"] = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(media_path + ".json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.warning("Could not write metadata sidecar: %s", e)
