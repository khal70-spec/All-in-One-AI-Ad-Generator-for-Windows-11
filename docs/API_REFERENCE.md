# API Reference

## Core Modules

### TextToVideoGenerator

```python
from core.text_to_video import TextToVideoGenerator

generator = TextToVideoGenerator(model_manager)

# Generate video from text
output_path = generator.generate(
    prompt="A red sports car driving down a highway",
    negative_prompt="blurry, low quality",
    num_frames=24,
    width=512,
    height=512,
    num_steps=25,
    guidance_scale=7.5,
    seed=-1,
    model="zeroscope",
    progress_callback=lambda p, msg: print(f"{p}%: {msg}"),
    cancel_check=lambda: False,
)

# Free VRAM
generator.unload_model()
```

**Parameters:**
- `prompt` (str): Text description of video to generate
- `negative_prompt` (str): Things to avoid in video
- `num_frames` (int): 1-256 frames
- `width` (int): 256-1024 pixels
- `height` (int): 256-1024 pixels
- `num_steps` (int): 1-100 diffusion steps
- `guidance_scale` (float): 0-20, how closely to follow prompt
- `seed` (int): -1 for random
- `model` (str): Model name
- `progress_callback` (callable): `func(progress: int, message: str)`
- `cancel_check` (callable): `func() -> None`, raises `GenerationCancelled`

**Returns:** Path to generated MP4 file

**Raises:**
- `ValueError`: Invalid inputs
- `RuntimeError`: Model load failed
- `GenerationCancelled`: User cancelled generation

---

### ImageToVideoGenerator

```python
from core.image_to_video import ImageToVideoGenerator

generator = ImageToVideoGenerator(model_manager)

# Generate video from image
output_path = generator.generate_from_image(
    image_path="/path/to/product.jpg",
    num_frames=25,
    num_steps=25,
    motion_bucket_id=127,
    noise_aug=0.02,
    model="svd",
    progress_callback=lambda p, msg: print(f"{p}%: {msg}"),
    cancel_check=lambda: False,
)

# Free VRAM
generator.unload_model()
```

**Parameters:**
- `image_path` (str): Path to input image
- `num_frames` (int): 1-256 frames
- `num_steps` (int): 1-100 diffusion steps
- `motion_bucket_id` (int): 0-255, motion intensity
- `noise_aug` (float): 0-1, noise augmentation
- `seed` (int): -1 for random
- `model` (str): "svd" or "animatediff"
- `progress_callback` (callable): `func(progress: int, message: str)`
- `cancel_check` (callable): `func() -> None`

**Returns:** Path to generated MP4 file

**Raises:**
- `FileNotFoundError`: Image not found
- `ValueError`: Invalid inputs
- `RuntimeError`: Model load failed
- `GenerationCancelled`: User cancelled

---

### ModelManager

```python
from core.model_manager import ModelManager

mm = ModelManager()

# Check system info
info = mm.get_system_info()
print(f"Device: {info['device']}")
print(f"GPU: {info['gpu_name']}")
print(f"VRAM: {info['vram_gb']}GB")

# Check VRAM availability
available = mm.available_vram_gb
total = mm.total_vram_gb
print(f"VRAM: {available}GB / {total}GB")

# Check if model fits
warning = mm.check_vram_fit("cogvideox")
if warning:
    print(f"Warning: {warning}")

# Check disk space
has_space = mm.check_disk_space("outputs", min_gb=5.0)
if not has_space:
    print("Not enough disk space")

# Clean GPU cache
mm.cleanup_cache()
```

**Methods:**
- `get_system_info() -> Dict`: System information
- `available_vram_gb -> float`: Free GPU VRAM in GB
- `total_vram_gb -> float`: Total GPU VRAM in GB
- `check_vram_fit(model: str) -> Optional[str]`: Warning if tight on VRAM
- `check_disk_space(path: str, min_gb: float) -> bool`: Check free space
- `cleanup_cache() -> None`: Clear GPU cache

---

### BatchProcessor

```python
from core.batch_improved import BatchProcessor

processor = BatchProcessor(model_manager, t2v_gen, i2v_gen)

# Define batch jobs
jobs = [
    {
        "type": "text_to_video",
        "prompt": "A car driving",
        "model": "zeroscope",
        "num_frames": 24,
        "num_steps": 25,
    },
    {
        "type": "image_to_video",
        "image_path": "/path/to/image.jpg",
        "model": "svd",
        "num_frames": 25,
    },
]

# Process batch
results = processor.process_batch(
    jobs,
    progress_callback=lambda p, msg: print(f"{p}%: {msg}")
)

print(f"Completed: {results['completed']}/{results['total_jobs']}")
for error in results['errors']:
    print(f"Error: {error}")

# Cancel batch
processor.cancel()
```

**Job Types:**

Text-to-video job:
```python
{
    "type": "text_to_video",
    "prompt": "Description",
    "model": "zeroscope|cogvideox|modelscope|mochi|hunyuanvideo|ltx_video",
    "negative_prompt": "Things to avoid",  # optional
    "num_frames": 24,  # optional
    "num_steps": 25,  # optional
    "guidance_scale": 7.5,  # optional
    "seed": -1,  # optional
}
```

Image-to-video job:
```python
{
    "type": "image_to_video",
    "image_path": "/path/to/image.jpg",
    "model": "svd|animatediff",
    "num_frames": 25,  # optional
    "num_steps": 25,  # optional
    "motion_bucket_id": 127,  # optional
    "seed": -1,  # optional
}
```

**Result Structure:**
```python
{
    "total_jobs": 10,
    "completed": 8,
    "failed": 2,
    "cancelled": False,
    "summary_path": "/path/to/batch_summary_123.json",
    "jobs": [
        {"success": True, "output_path": "/path/to/video.mp4"},
        {"success": False, "error": "Out of memory"},
        # ...
    ],
    "errors": [
        {"job_index": 1, "error": "Out of memory"},
        # ...
    ]
}
```

---

## Configuration

### Load/Save Settings

```python
from config import (
    load_settings, save_settings,
    get_ui_pref, set_ui_pref,
    USER_SETTINGS, MODELS, AD_TEMPLATES
)

# Load settings from config.json
load_settings()

# Save settings
save_settings()

# Get UI preference
model_name = get_ui_pref("text_to_video_tab", "selected_model", "zeroscope")
num_frames = get_ui_pref("text_to_video_tab", "num_frames", 24)

# Set UI preference (auto-saves)
set_ui_pref("text_to_video_tab", "selected_model", "cogvideox")
set_ui_pref("text_to_video_tab", "num_frames", 32)

# Access config directly
print(MODELS["zeroscope"]["vram"])  # 8
print(list(AD_TEMPLATES.keys()))
```

---

## Error Handling

```python
from core.text_to_video import TextToVideoGenerator
from core.progress import GenerationCancelled
from core.logger import get_logger

log = get_logger("my_module")

try:
    generator = TextToVideoGenerator(model_manager)
    output = generator.generate(
        prompt="Test",
        model="zeroscope"
    )
except ValueError as e:
    log.error("Invalid input: %s", e)
    # Handle invalid parameters
except RuntimeError as e:
    log.error("Failed to load model: %s", e)
    # Handle model loading failures
except GenerationCancelled:
    log.info("Generation cancelled by user")
    # Handle user cancellation
except Exception as e:
    log.error("Unexpected error: %s", e)
    # Handle other errors
finally:
    # Always clean up
    generator.unload_model()
```

---

## Logging

```python
from core.logger import get_logger

# Get logger for your module
log = get_logger("my_module_name")

# Log at different levels
log.debug("Debug message")
log.info("Information message")
log.warning("Warning message")
log.error("Error message")

# Logs are written to: temp/app.log
```

---

## Type Hints Reference

```python
from typing import Optional, Dict, Any, List, Callable, Tuple

# Optional types (can be None)
def func1(value: Optional[str]) -> Optional[int]:
    return None

# Dict types
def func2(config: Dict[str, Any]) -> Dict[str, float]:
    return {"value": 1.5}

# Callable types (functions)
def func3(callback: Callable[[int, str], None]) -> None:
    callback(100, "Done")

# List and Tuple
def func4(items: List[str]) -> Tuple[int, str]:
    return (len(items), "count")
```

---

For more examples, check the source code and docstrings!
