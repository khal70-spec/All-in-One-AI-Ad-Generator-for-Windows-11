"""Helpers for showing generated videos inside the UI."""

from PIL import Image


def extract_thumbnail(video_path, max_size=480):
    """Return a PIL thumbnail of the first frame of ``video_path`` (or None)."""
    import cv2

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    try:
        ret, frame = cap.read()
    finally:
        cap.release()

    if not ret or frame is None:
        return None

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame)
    img.thumbnail((max_size, max_size))
    return img


def make_ctk_thumbnail(video_path, max_size=480):
    """Return a ``ctk.CTkImage`` for the first frame, or None on failure."""
    import customtkinter as ctk

    img = extract_thumbnail(video_path, max_size=max_size)
    if img is None:
        return None
    return ctk.CTkImage(light_image=img, dark_image=img,
                        size=(img.width, img.height))
