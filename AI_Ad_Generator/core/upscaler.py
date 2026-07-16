import os
import time
import base64
import mimetypes
import requests
from config import OUTPUTS_DIR


class UpscalerClient:
    """Free online image upscaling via upscale.media (no API key required).

    Note: this upscales an *image*. It is most useful for polishing a
    generated product image (e.g. SDXL output) before animating it, or for
    upscaling a poster frame. For video upscaling you would upscale each
    frame; here we expose the image-level primitive the app can call.
    """

    BASE = "https://api.upscale.media/api/tasks/upscale"

    def upscale_image(self, image_path, scale=2, progress_callback=None):
        if not os.path.exists(image_path):
            raise RuntimeError(f"Image not found: {image_path}")

        if progress_callback:
            progress_callback(10, "Uploading image for upscaling...")

        mime = mimetypes.guess_type(image_path)[0] or "image/png"
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        data_uri = f"data:{mime};base64,{b64}"

        resp = requests.post(self.BASE, json={"image": data_uri, "scale": scale},
                            timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"Upscaler error {resp.status_code}: {resp.text[:200]}")
        result = resp.json()
        dest = result.get("dest")
        if not dest:
            raise RuntimeError(f"Upscaler returned no destination: {result}")

        if progress_callback:
            progress_callback(60, "Downloading upscaled image...")

        timestamp = int(time.time())
        name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(OUTPUTS_DIR, f"{name}_upscaled_{timestamp}.png")
        with requests.get(dest, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        if progress_callback:
            progress_callback(100, "Upscale complete!")
        return output_path
