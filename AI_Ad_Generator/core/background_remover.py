import os
from PIL import Image
import numpy as np
from config import TEMP_DIR


class BackgroundRemover:
    """Remove background from product images"""

    def __init__(self):
        self.session = None

    def _load_model(self):
        if self.session is None:
            try:
                from rembg import new_session
                self.session = new_session("u2net")
            except Exception:
                self.session = "basic"

    def remove_background(self, image_path, output_path=None):
        """Remove background from image"""
        self._load_model()

        if output_path is None:
            name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(TEMP_DIR, f"{name}_nobg.png")

        try:
            from rembg import remove
            input_image = Image.open(image_path)
            output_image = remove(input_image, session=self.session if self.session != "basic" else None)
            output_image.save(output_path)
            return output_path
        except Exception as e:
            print(f"Background removal error: {e}")
            return image_path

    def replace_background(self, image_path, bg_color=(255, 255, 255), output_path=None):
        """Remove background and replace with solid color"""
        nobg_path = self.remove_background(image_path)

        if output_path is None:
            name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(TEMP_DIR, f"{name}_newbg.png")

        try:
            fg = Image.open(nobg_path).convert("RGBA")
            bg = Image.new("RGBA", fg.size, bg_color + (255,))
            combined = Image.alpha_composite(bg, fg)
            combined.convert("RGB").save(output_path)
            return output_path
        except Exception as e:
            print(f"Background replace error: {e}")
            return image_path
