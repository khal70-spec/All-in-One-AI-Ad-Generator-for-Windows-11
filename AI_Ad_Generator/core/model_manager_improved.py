import os
import torch
import psutil
from typing import Optional, Dict, Any
from .logger import get_logger

log = get_logger("model_mgr")


class ModelManager:
    """Manages model downloads, loading, and VRAM/disk monitoring.
    
    Handles device detection, memory checks, and model lifecycle.
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._cached_system_info: Optional[Dict[str, Any]] = None

    @property
    def available_vram_gb(self) -> float:
        """Get currently available GPU VRAM in GB.
        
        Returns:
            Available VRAM in gigabytes, or 0 if no GPU
        """
        try:
            if torch.cuda.is_available():
                return torch.cuda.mem_get_info()[0] / (1024**3)
        except Exception as e:
            log.warning("Could not get available VRAM: %s", e)
        return 0.0

    @property
    def total_vram_gb(self) -> float:
        """Get total GPU VRAM in GB.
        
        Returns:
            Total VRAM in gigabytes, or 0 if no GPU
        """
        try:
            if torch.cuda.is_available():
                return torch.cuda.get_device_properties(0).total_memory / (1024**3)
        except Exception as e:
            log.warning("Could not get total VRAM: %s", e)
        return 0.0

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information (GPU, CPU, memory).
        
        Returns:
            Dictionary with device info
        """
        if self._cached_system_info is not None:
            return self._cached_system_info

        info = {
            "device": self.device,
            "gpu_name": "Unknown",
            "vram_gb": 0.0,
            "cpu_cores": psutil.cpu_count(),
            "system_ram_gb": psutil.virtual_memory().total / (1024**3),
        }

        try:
            if torch.cuda.is_available():
                info["gpu_name"] = torch.cuda.get_device_name(0)
                info["vram_gb"] = self.total_vram_gb
        except Exception as e:
            log.warning("Could not get GPU info: %s", e)

        self._cached_system_info = info
        return info

    def check_vram_fit(self, model: str) -> Optional[str]:
        """Check if model fits in available VRAM.
        
        Args:
            model: Model identifier from config.MODELS
            
        Returns:
            Warning message if tight on VRAM, None if OK
        """
        try:
            from config import MODELS
            
            if model not in MODELS:
                return None
                
            required_vram = MODELS[model].get("vram", 8)
            available = self.available_vram_gb
            
            if available < required_vram * 0.5:
                return f"⚠️ Low VRAM: {available:.1f}GB available, {required_vram}GB recommended"
            elif available < required_vram:
                return f"⚠️ Tight VRAM: {available:.1f}GB available, {required_vram}GB recommended"
        except Exception as e:
            log.warning("VRAM check failed: %s", e)
            
        return None

    def check_disk_space(self, output_dir: str, min_gb: float = 2.0) -> bool:
        """Check if output directory has minimum free space.
        
        Args:
            output_dir: Path to output directory
            min_gb: Minimum free space required in GB
            
        Returns:
            True if enough space, False otherwise
        """
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            stat = os.statvfs(output_dir)
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
            return free_gb >= min_gb
        except Exception as e:
            log.warning("Disk space check failed: %s", e)
            return False

    def cleanup_cache(self) -> None:
        """Clean GPU cache to free memory."""
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                log.info("GPU cache cleaned")
        except Exception as e:
            log.warning("Could not clean GPU cache: %s", e)
