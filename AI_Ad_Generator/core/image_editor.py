from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os
from config import TEMP_DIR


class ImageEditor:
    """Edit and prepare images for video generation"""

    @staticmethod
    def resize_image(image_path, width, height, output_path=None):
        if output_path is None:
            name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(TEMP_DIR, f"{name}_resized.png")

        img = Image.open(image_path)
        img = img.resize((width, height), Image.LANCZOS)
        img.save(output_path)
        return output_path

    @staticmethod
    def add_text_overlay(image_path, text, position="bottom",
                        font_size=40, color=(255, 255, 255),
                        output_path=None):
        if output_path is None:
            name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(TEMP_DIR, f"{name}_text.png")

        img = Image.open(image_path).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        w, h = img.size
        if position == "bottom":
            x = (w - text_width) // 2
            y = h - text_height - 30
        elif position == "top":
            x = (w - text_width) // 2
            y = 30
        elif position == "center":
            x = (w - text_width) // 2
            y = (h - text_height) // 2
        else:
            x, y = 30, 30

        # Draw shadow
        draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 180))
        # Draw text
        draw.text((x, y), text, font=font, fill=color + (255,))

        result = Image.alpha_composite(img, overlay)
        result.convert("RGB").save(output_path)
        return output_path

    @staticmethod
    def enhance_image(image_path, brightness=1.0, contrast=1.0,
                     sharpness=1.0, saturation=1.0, output_path=None):
        if output_path is None:
            name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(TEMP_DIR, f"{name}_enhanced.png")

        img = Image.open(image_path)

        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if sharpness != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(sharpness)
        if saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(saturation)

        img.save(output_path)
        return output_path

    @staticmethod
    def create_product_composite(product_path, bg_color=(255, 255, 255),
                                 size=(512, 512), output_path=None):
        """Create a clean product image on solid background"""
        if output_path is None:
            name = os.path.splitext(os.path.basename(product_path))[0]
            output_path = os.path.join(TEMP_DIR, f"{name}_composite.png")

        bg = Image.new("RGB", size, bg_color)
        product = Image.open(product_path).convert("RGBA")

        # Resize product to fit
        product.thumbnail((int(size[0] * 0.8), int(size[1] * 0.8)), Image.LANCZOS)

        # Center product
        x = (size[0] - product.width) // 2
        y = (size[1] - product.height) // 2

        bg.paste(product, (x, y), product)
        bg.save(output_path)
        return output_path
