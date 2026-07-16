import os
import json
from typing import Dict, Any, Optional

# ============================================
# APPLICATION CONFIGURATION
# ============================================

APP_NAME = "AI Ad Generator"
APP_VERSION = "1.0.1"
APP_ICON = "assets/icon.ico"

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Create directories
for d in [MODELS_DIR, OUTPUTS_DIR, TEMP_DIR, ASSETS_DIR]:
    try:
        os.makedirs(d, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create directory {d}: {e}")

# Model Settings
MODELS: Dict[str, Dict[str, Any]] = {
    "stable_video_diffusion": {
        "name": "Stable Video Diffusion",
        "repo": "stabilityai/stable-video-diffusion-img2vid-xt",
        "type": "image_to_video",
        "vram": 8,
    },
    "animatediff": {
        "name": "AnimateDiff",
        "repo": "guoyww/animatediff-motion-adapter-v1-5-3",
        "type": "image_to_video",
        "vram": 8,
    },
    "cogvideox": {
        "name": "CogVideoX",
        "repo": "THUDM/CogVideoX-2b",
        "type": "text_to_video",
        "vram": 16,
    },
    "stable_diffusion_xl": {
        "name": "Stable Diffusion XL",
        "repo": "stabilityai/stable-diffusion-xl-base-1.0",
        "type": "text_to_image",
        "vram": 8,
    },
    "zeroscope": {
        "name": "ZeroScope V2",
        "repo": "cerspense/zeroscope_v2_576w",
        "type": "text_to_video",
        "vram": 8,
    },
    "modelscope": {
        "name": "ModelScope T2V",
        "repo": "damo-vilab/text-to-video-ms-1.7b",
        "type": "text_to_video",
        "vram": 8,
    },
    "mochi": {
        "name": "Mochi 1",
        "repo": "genmo/mochi-1-preview",
        "type": "text_to_video",
        "vram": 24,
    },
    "hunyuanvideo": {
        "name": "HunyuanVideo",
        "repo": "tencent/HunyuanVideo",
        "type": "text_to_video",
        "vram": 24,
    },
    "ltx_video": {
        "name": "LTX-Video",
        "repo": "Lightricks/LTX-Video",
        "type": "text_to_video",
        "vram": 12,
    },
}

# Video Settings
DEFAULT_VIDEO_WIDTH = 512
DEFAULT_VIDEO_HEIGHT = 512
DEFAULT_FPS = 8
DEFAULT_NUM_FRAMES = 25
DEFAULT_VIDEO_LENGTH = 3  # seconds

# Generation Settings
DEFAULT_STEPS = 25
DEFAULT_GUIDANCE = 7.5
DEFAULT_SEED = -1  # Random

# Ad Templates
AD_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "product_showcase": {
        "name": "Product Showcase",
        "prompt_template": "Professional product advertisement for {product}, studio lighting, "
                          "clean white background, commercial photography, 4K, cinematic",
        "negative": "blurry, low quality, distorted, ugly, bad lighting",
        "steps": 30,
        "guidance": 8.0,
    },
    "lifestyle": {
        "name": "Lifestyle Ad",
        "prompt_template": "Lifestyle advertisement showing {product} in daily use, "
                          "warm lighting, happy atmosphere, professional commercial, 4K",
        "negative": "blurry, low quality, distorted, text, watermark",
        "steps": 30,
        "guidance": 7.5,
    },
    "luxury": {
        "name": "Luxury Ad",
        "prompt_template": "Luxury premium advertisement for {product}, dark elegant background, "
                          "golden accents, dramatic lighting, high-end commercial, 4K",
        "negative": "cheap, low quality, blurry, distorted",
        "steps": 35,
        "guidance": 8.5,
    },
    "minimalist": {
        "name": "Minimalist Ad",
        "prompt_template": "Minimalist clean advertisement for {product}, simple background, "
                          "modern design, professional, Apple-style commercial, 4K",
        "negative": "cluttered, busy, low quality, blurry",
        "steps": 25,
        "guidance": 7.0,
    },
    "dynamic": {
        "name": "Dynamic/Action",
        "prompt_template": "Dynamic action advertisement for {product}, motion blur, "
                          "energetic, vibrant colors, sports commercial style, 4K",
        "negative": "static, boring, low quality, blurry",
        "steps": 30,
        "guidance": 8.0,
    },
}

# ============================================
# ONLINE API CONNECTIONS (Pika / Luma / etc.)
# ============================================
# These are OPTIONAL. Leave keys empty to disable. The app works fully offline
# without them. When a key is provided the corresponding provider can generate
# videos from the cloud (useful on machines without a GPU).

ONLINE_PROVIDERS: Dict[str, Dict[str, Any]] = {
    "pika": {
        "name": "Pika",
        "base_url": "https://api.pika.art/v1",
        "auth_scheme": "key",  # header: Authorization: Key <KEY>
        "needs_key": True,
    },
    "luma": {
        "name": "Luma Dream Machine",
        "base_url": "https://api.luma.ai/v1",
        "auth_scheme": "bearer",  # header: Authorization: Bearer <KEY>
        "needs_key": True,
    },
}

# Persisted user settings (API keys, etc.)
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
USER_SETTINGS: Dict[str, Any] = {
    "pika_api_key": "",
    "luma_api_key": "",
    "use_online_fallback": False,
    "ui_prefs": {},  # per-tab widget values, restored on next launch
}


def _validate_api_key(key: str, provider: str) -> bool:
    """Validate API key format.
    
    Args:
        key: API key to validate
        provider: Provider name (pika or luma)
        
    Returns:
        True if key appears valid, False otherwise
    """
    if not key or not isinstance(key, str):
        return False
    key = key.strip()
    if len(key) < 10 or len(key) > 500:
        return False
    return True


def load_settings() -> None:
    """Load user settings (API keys, prefs) from config.json if present."""
    global USER_SETTINGS
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Only load keys that exist in USER_SETTINGS schema
            for key, default_value in USER_SETTINGS.items():
                if key in data:
                    value = data[key]
                    # Type check to prevent injection
                    if type(value) == type(default_value):
                        USER_SETTINGS[key] = value
    except json.JSONDecodeError:
        print("Warning: config.json is corrupted, using defaults")
    except Exception as e:
        print(f"Warning: Could not load config: {e}")


def save_settings() -> bool:
    """Persist current user settings to config.json.
    
    Returns:
        True if save successful, False otherwise
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(USER_SETTINGS, f, indent=2)
        return True
    except Exception as e:
        print(f"Warning: Could not save config: {e}")
        return False


def get_ui_pref(section: str, key: str, default: Any = None) -> Any:
    """Read a persisted per-tab widget value.
    
    Args:
        section: Tab/section name
        key: Setting key
        default: Default value if not found
        
    Returns:
        Persisted value or default
    """
    prefs = USER_SETTINGS.get("ui_prefs")
    if not isinstance(prefs, dict):
        return default
    return prefs.get(section, {}).get(key, default)


def set_ui_pref(section: str, key: str, value: Any) -> bool:
    """Persist a per-tab widget value (writes config.json on change).
    
    Args:
        section: Tab/section name
        key: Setting key
        value: Value to persist
        
    Returns:
        True if save successful, False otherwise
    """
    prefs = USER_SETTINGS.setdefault("ui_prefs", {})
    if not isinstance(prefs, dict):
        prefs = USER_SETTINGS["ui_prefs"] = {}
    section_prefs = prefs.setdefault(section, {})
    if section_prefs.get(key) != value:
        section_prefs[key] = value
        return save_settings()
    return True


# Load any previously saved settings at import time
load_settings()
