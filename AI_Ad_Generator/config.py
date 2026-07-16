import os

# ============================================
# APPLICATION CONFIGURATION
# ============================================

APP_NAME = "AI Ad Generator"
APP_VERSION = "1.0.0"
APP_ICON = "assets/icon.ico"

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Create directories
for d in [MODELS_DIR, OUTPUTS_DIR, TEMP_DIR, ASSETS_DIR]:
    os.makedirs(d, exist_ok=True)

# Model Settings
MODELS = {
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
AD_TEMPLATES = {
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
