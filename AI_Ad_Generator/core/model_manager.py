import os
import torch
import psutil
from config import MODELS_DIR, MODELS
from huggingface_hub import snapshot_download
from tqdm import tqdm


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

    def download_model(self, model_key, progress_callback=None):
        if model_key not in MODELS:
            raise ValueError(f"Unknown model: {model_key}")

        model_info = MODELS[model_key]
        model_path = os.path.join(MODELS_DIR, model_key)

        if os.path.exists(model_path):
            if progress_callback:
                progress_callback(100, "Model already downloaded")
            return model_path

        if progress_callback:
            progress_callback(0, f"Downloading {model_info['name']}...")

        try:
            snapshot_download(
                repo_id=model_info["repo"],
                local_dir=model_path,
                local_dir_use_symlinks=False,
            )
            if progress_callback:
                progress_callback(100, "Download complete")
            return model_path
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            raise

    def is_model_downloaded(self, model_key):
        model_path = os.path.join(MODELS_DIR, model_key)
        return os.path.exists(model_path) and len(os.listdir(model_path)) > 0

    def unload_all(self):
        for key in list(self.loaded_models.keys()):
            del self.loaded_models[key]
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self.loaded_models = {}
