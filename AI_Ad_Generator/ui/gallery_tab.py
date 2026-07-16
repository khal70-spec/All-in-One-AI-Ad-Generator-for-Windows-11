import customtkinter as ctk
from ui.styles import COLORS, FONTS
from config import OUTPUTS_DIR
from core.preview_utils import extract_thumbnail
from core.utils import open_path, human_size
from PIL import Image
import os

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


class GalleryTab:
    """Browse all generated outputs (videos + images) as thumbnails."""

    def __init__(self, parent):
        self.parent = parent
        self._create_ui()
        self.refresh()

    def _create_ui(self):
        main = ctk.CTkFrame(self.parent, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        header = ctk.CTkFrame(main, fg_color=COLORS["bg_medium"], corner_radius=10)
        header.pack(fill="x", padx=0, pady=(0, 10))

        ctk.CTkLabel(header, text="🖼 Gallery — your generated ads",
                     font=FONTS["heading"]).pack(side="left", padx=15, pady=10)
        ctk.CTkButton(header, text="🔄 Refresh", width=100,
                      fg_color=COLORS["bg_light"],
                      command=self.refresh).pack(side="right", padx=15, pady=10)

        self.scroll = ctk.CTkScrollableFrame(main, fg_color=COLORS["bg_dark"],
                                            corner_radius=10)
        self.scroll.pack(fill="both", expand=True, padx=0, pady=0)

    def refresh(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        files = []
        if os.path.isdir(OUTPUTS_DIR):
            for f in os.listdir(OUTPUTS_DIR):
                ext = os.path.splitext(f)[1].lower()
                if ext in IMAGE_EXTS or ext in VIDEO_EXTS:
                    files.append(f)
        files.sort(reverse=True)

        if not files:
            ctk.CTkLabel(self.scroll,
                        text="No outputs yet — generate something! 🎬",
                        font=FONTS["body"],
                        text_color=COLORS["text_secondary"]).pack(pady=40)
            return

        col, row, max_cols = 0, 0, 3
        for f in files:
            path = os.path.join(OUTPUTS_DIR, f)
            item = self._make_item(path, f)
            item.grid(row=row, column=col, padx=10, pady=10, sticky="n")
            col += 1
            if col >= max_cols:
                col, row = 0, row + 1

    def _make_item(self, path, name):
        ext = os.path.splitext(name)[1].lower()
        frame = ctk.CTkFrame(self.scroll, fg_color=COLORS["bg_medium"],
                            corner_radius=10, width=220)

        try:
            if ext in VIDEO_EXTS:
                img = extract_thumbnail(path, max_size=200)
            else:
                img = Image.open(path)
                img.thumbnail((200, 200))
            if img is not None:
                photo = ctk.CTkImage(light_image=img, dark_image=img,
                                    size=(img.width, img.height))
                lbl = ctk.CTkLabel(frame, text="", image=photo)
                lbl.image = photo
                lbl.pack(padx=8, pady=8)
        except Exception:
            pass

        ctk.CTkLabel(frame, text=name, font=FONTS["small"],
                    text_color=COLORS["text_secondary"]).pack(pady=(0, 2))
        try:
            size_txt = human_size(os.path.getsize(path))
        except OSError:
            size_txt = "-"
        ctk.CTkLabel(frame, text=size_txt, font=("Segoe UI", 9),
                    text_color=COLORS["text_secondary"]).pack(pady=(0, 4))
        ctk.CTkButton(frame, text="▶ Open", height=28,
                      fg_color=COLORS["bg_light"],
                      command=lambda p=path: open_path(p)).pack(
                          padx=8, pady=(0, 8))
        return frame
