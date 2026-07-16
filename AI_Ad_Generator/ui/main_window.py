import customtkinter as ctk
from ui.styles import COLORS, FONTS
from ui.text_to_video_tab import TextToVideoTab
from ui.image_to_video_tab import ImageToVideoTab
from ui.prompt_tab import PromptTab
from ui.editor_tab import EditorTab
from ui.settings_tab import SettingsTab
from ui.batch_tab import BatchTab
from ui.gallery_tab import GalleryTab
from core.model_manager import ModelManager
from core.prompt_generator import PromptGenerator
from config import APP_NAME, APP_VERSION
import os


class MainWindow:
    """Main application window"""

    def __init__(self):
        # Initialize core components
        self.model_manager = ModelManager()
        self.prompt_generator = PromptGenerator()

        # Setup theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create main window
        self.root = ctk.CTk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # Try to set icon
        icon_path = "assets/icon.ico"
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        self._create_ui()

    def _create_ui(self):
        """Create the main UI layout"""

        # ============ HEADER ============
        header_frame = ctk.CTkFrame(self.root, height=80, corner_radius=0,
                                   fg_color=COLORS["bg_medium"])
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header_frame,
            text=f"🎬 {APP_NAME}",
            font=FONTS["title"],
            text_color=COLORS["accent"],
        )
        title_label.pack(side="left", padx=20, pady=15)

        # System info
        sys_info = self.model_manager.get_system_info()
        gpu_text = f"GPU: {sys_info['gpu_name']} | VRAM: {sys_info['vram_gb']}GB"
        if sys_info['device'] == 'cpu':
            gpu_text = "⚠️ No GPU detected - CPU mode (slower)"

        info_label = ctk.CTkLabel(
            header_frame,
            text=gpu_text,
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
        )
        info_label.pack(side="right", padx=20, pady=15)

        # ============ TABVIEW ============
        self.tabview = ctk.CTkTabview(
            self.root,
            fg_color=COLORS["bg_dark"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color=COLORS["accent_hover"],
        )
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        tab1 = self.tabview.add("📝 Text to Video")
        tab2 = self.tabview.add("🖼 Image to Video")
        tab3 = self.tabview.add("💡 Prompt Generator")
        tab4 = self.tabview.add("✂️ Video Editor")
        tab5 = self.tabview.add("⚙️ Settings & Models")
        tab6 = self.tabview.add("🔁 Batch")
        tab7 = self.tabview.add("🖼 Gallery")

        # Initialize tab content
        self.text_to_video_tab = TextToVideoTab(tab1, self.model_manager, self.prompt_generator)
        self.image_to_video_tab = ImageToVideoTab(tab2, self.model_manager)
        self.prompt_tab = PromptTab(tab3, self.prompt_generator)
        self.editor_tab = EditorTab(tab4)
        self.settings_tab = SettingsTab(tab5, self.model_manager)
        self.batch_tab = BatchTab(tab6, self.model_manager, self.prompt_generator)
        self.gallery_tab = GalleryTab(tab7)

        # ============ STATUS BAR ============
        status_frame = ctk.CTkFrame(self.root, height=30, corner_radius=0,
                                   fg_color=COLORS["bg_medium"])
        status_frame.pack(fill="x", padx=0, pady=0)

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready | All systems operational",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
        )
        self.status_label.pack(side="left", padx=10, pady=5)

    def run(self):
        """Start the application"""
        self.root.mainloop()
