import os
from config import MODELS_DIR
from .text_to_video import TextToVideoGenerator
from .image_to_video import ImageToVideoGenerator
from .text_to_image import TextToImageGenerator
from .background_remover import BackgroundRemover
from .image_editor import ImageEditor
from .online_apis import get_provider


class BatchProcessor:
    """Runs a queue of generation jobs through the existing engines.

    Each ``job`` is a dict with at least a ``type`` key:
      - ``{"type": "text", "prompt": ..., "model": "zeroscope", ...}``
      - ``{"type": "image", "image": <path>, "model": "svd", ...}``
      - ``{"type": "image_gen", "prompt": ..., "model": "stable_diffusion_xl", ...}``
    """

    def __init__(self, model_manager, prompt_generator=None):
        self.model_manager = model_manager
        self.prompt_generator = prompt_generator
        self.t2v = TextToVideoGenerator(model_manager)
        self.i2v = ImageToVideoGenerator(model_manager)
        self.t2i = TextToImageGenerator(model_manager)
        self._stop = False

    def stop(self):
        self._stop = True

    # ------------------------------------------------------------------ #
    def run(self, jobs, progress_callback=None):
        results = []
        total = max(len(jobs), 1)
        for i, job in enumerate(jobs):
            if self._stop:
                results.append({"job": job, "output": None,
                                "status": "cancelled"})
                continue

            def job_progress(value, message):
                if progress_callback:
                    overall = int((i + value / 100.0) / total * 100)
                    progress_callback(overall, f"[{i + 1}/{total}] {message}")

            try:
                out = self._run_one(job, job_progress)
                results.append({"job": job, "output": out, "status": "ok"})
            except Exception as e:
                results.append({"job": job, "output": None,
                                "status": "error", "error": str(e)})
        return results

    # ------------------------------------------------------------------ #
    def _run_one(self, job, cb):
        jtype = job.get("type")

        if jtype == "text":
            out = self.t2v.generate(
                prompt=job.get("prompt", ""),
                negative_prompt=job.get("negative", ""),
                num_frames=job.get("frames", 24),
                width=job.get("width", 512),
                height=job.get("height", 512),
                num_steps=job.get("steps", 25),
                guidance_scale=job.get("guidance", 7.5),
                seed=job.get("seed", -1),
                model=job.get("model", "zeroscope"),
                progress_callback=cb,
            )
            return self._maybe_add_sound(out, job)

        if jtype == "image":
            image_path = job["image"]
            if job.get("remove_bg"):
                image_path = BackgroundRemover().remove_background(image_path)
            if job.get("enhance"):
                image_path = ImageEditor.enhance_image(
                    image_path, brightness=1.05, contrast=1.1, sharpness=1.2)
            out = self.i2v.generate_from_image(
                image_path=image_path,
                num_frames=job.get("frames", 25),
                motion_bucket_id=job.get("motion", 127),
                noise_aug=job.get("noise", 0.02),
                seed=job.get("seed", -1),
                model=job.get("model", "svd"),
                progress_callback=cb,
            )
            return self._maybe_add_sound(out, job)

        if jtype == "image_gen":
            return self.t2i.generate(
                prompt=job.get("prompt", ""),
                negative_prompt=job.get("negative", ""),
                width=job.get("width", 1024),
                height=job.get("height", 1024),
                num_steps=job.get("steps", 25),
                guidance_scale=job.get("guidance", 7.5),
                seed=job.get("seed", -1),
                model=job.get("model", "stable_diffusion_xl"),
                progress_callback=cb,
            )

        if jtype == "online":
            provider = get_provider(job.get("provider", "pika"))
            return provider.generate(prompt=job.get("prompt", ""), progress_callback=cb)

        raise ValueError(f"Unknown job type: {jtype}")

    def _maybe_add_sound(self, video_path, job):
        if not job.get("sound"):
            return video_path
        try:
            from .sound import add_sound_to_video
            return add_sound_to_video(
                video_path,
                prompt=job.get("prompt"),
                voiceover=bool(job.get("prompt")),
                music=True,
            )
        except Exception as e:
            print(f"Batch sound error: {e}")
            return video_path
