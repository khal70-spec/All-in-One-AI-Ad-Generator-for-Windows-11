import os
import shutil
import torch
import psutil
from config import MODELS_DIR, MODELS
from huggingface_hub import snapshot_download

from .logger import get_logger
from .utils import human_size

log = get_logger("models")

# Rough download sizes (GB) used for disk-space pre-checks. These are
# conservative estimates of the full snapshot, including text encoders.
ESTIMATED_MODEL_SIZES_GB = {
    "zeroscope": 5,
    "modelscope": 5,
    "cogvideox": 12,
    "mochi": 40,
    "hunyuanvideo": 40,
    "ltx_video": 12,
    "stable_diffusion_xl": 7,
    "stable_video_diffusion": 10,
    "animatediff": 6,
}


class ModelManager:
    """Manages downloading, loading, and unloading AI models"""

    def __init__(self):
        self.loaded_models = {}
        self.device = self._get_device()
        self.vram = self._get_vram()

    def _get_device(self):
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _get_vram(self):
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / (1024**3)
        return 0

    def get_system_info(self):
        info = {
            "device": self.device,
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None",
            "vram_gb": round(self.vram, 1),
            "ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "available_models": self._get_compatible_models(),
        }
        return info

    def _get_compatible_models(self):
        compatible = []
        for key, model in MODELS.items():
            if model["vram"] <= self.vram or self.device == "cpu":
                compatible.append(key)
        return compatible

    # ------------------------------------------------------------------ #
    # Disk helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def disk_free_gb():
        """Free disk space (GB) on the drive holding the models folder."""
        return shutil.disk_usage(MODELS_DIR).free / (1024**3)

    @staticmethod
    def estimated_size_gb(model_key):
        return ESTIMATED_MODEL_SIZES_GB.get(model_key)

    @staticmethod
    def model_size_on_disk(model_key):
        """Actual size (bytes) of a downloaded model folder, or None."""
        model_path = os.path.join(MODELS_DIR, model_key)
        if not os.path.isdir(model_path):
            return None
        total = 0
        for root, _dirs, files in os.walk(model_path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        return total

    @staticmethod
    def model_size_label(model_key):
        size = ModelManager.model_size_on_disk(model_key)
        return human_size(size) if size is not None else "-"

    def delete_model(self, model_key):
        """Delete a downloaded model from disk. Returns True if removed."""
        model_path = os.path.join(MODELS_DIR, model_key)
        # Safety: only ever delete inside MODELS_DIR.
        if os.path.abspath(model_path) == os.path.abspath(MODELS_DIR):
            raise ValueError("Refusing to delete the models root directory")
        if not os.path.isdir(model_path):
            return False
        log.info("Deleting model '%s' (%s)", model_key,
                 human_size(self.model_size_on_disk(model_key) or 0))
        shutil.rmtree(model_path)
        return True

    # ------------------------------------------------------------------ #
    # Download
    # ------------------------------------------------------------------ #
    def download_model(self, model_key, progress_callback=None):
        if model_key not in MODELS:
            raise ValueError(f"Unknown model: {model_key}")

        model_info = MODELS[model_key]
        model_path = os.path.join(MODELS_DIR, model_key)

        if self.is_model_downloaded(model_key):
            if progress_callback:
                progress_callback(100, "Model already downloaded")
            return model_path

        # Disk-space pre-check so a 12 GB download doesn't fail at 90%.
        est = self.estimated_size_gb(model_key)
        free = self.disk_free_gb()
        if est is not None and free < est + 1:
            raise RuntimeError(
                f"Not enough disk space: {model_info['name']} needs about "
                f"{est} GB but only {free:.1f} GB is free."
            )
        if est is not None and progress_callback:
            progress_callback(
                0, f"Downloading {model_info['name']} "
                   f"(≈{est} GB, {free:.0f} GB free)...")
        elif progress_callback:
            progress_callback(0, f"Downloading {model_info['name']}...")

        try:
            # Note: `local_dir_use_symlinks` is intentionally not passed —
            # it is deprecated/removed in newer huggingface_hub and the
            # default behavior avoids symlinks when local_dir is used.
            snapshot_download(
                repo_id=model_info["repo"],
                local_dir=model_path,
            )
            log.info("Downloaded model '%s' to %s", model_key, model_path)
            if progress_callback:
                progress_callback(100, "Download complete")
            return model_path
        except Exception as e:
            log.error("Download of '%s' failed: %s", model_key, e)
            # Clean up a partial download so a retry doesn't think the
            # model is present.
            if os.path.isdir(model_path) and not os.listdir(model_path):
                try:
                    os.rmdir(model_path)
                except OSError:
                    pass
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            raise

    def check_vram_fit(self, model_key):
        """Return a warning string if the model likely exceeds VRAM, else None."""
        model_info = MODELS.get(model_key)
        if not model_info or self.device != "cuda":
            return None
        required = model_info.get("vram", 0)
        if required > self.vram:
            return (f"⚠️ {model_info['name']} wants ~{required} GB VRAM, "
                    f"you have {self.vram:.0f} GB — it may be slow or fail.")
        return None

    def is_model_downloaded(self, model_key):
        model_path = os.path.join(MODELS_DIR, model_key)
        return os.path.isdir(model_path) and len(os.listdir(model_path)) > 0

    def unload_all(self):
        for key in list(self.loaded_models.keys()):
            del self.loaded_models[key]
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self.loaded_models = {}
