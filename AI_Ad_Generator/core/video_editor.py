import os
from config import OUTPUTS_DIR, TEMP_DIR
from .ffmpeg_setup import configure_ffmpeg
configure_ffmpeg()


class VideoEditor:
    """Edit and combine generated videos"""

    @staticmethod
    def add_text_to_video(video_path, text, position="bottom",
                         fontsize=40, color="white", output_path=None):
        """Add text overlay to video"""
        from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

        if output_path is None:
            name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(OUTPUTS_DIR, f"{name}_text.mp4")

        video = VideoFileClip(video_path)

        try:
            txt_clip = TextClip(
                text, fontsize=fontsize, color=color,
                stroke_color="black", stroke_width=2,
                font="Arial",
            )
        except Exception:
            txt_clip = TextClip(text, fontsize=fontsize, color=color)

        txt_clip = txt_clip.set_position(("center", position))
        txt_clip = txt_clip.set_duration(video.duration)

        final = CompositeVideoClip([video, txt_clip])
        final.write_videofile(output_path, codec="libx264", fps=video.fps)

        video.close()
        final.close()
        return output_path

    @staticmethod
    def add_music(video_path, audio_path, volume=0.5, output_path=None):
        """Add background music to video"""
        from moviepy.editor import VideoFileClip, AudioFileClip

        if output_path is None:
            name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(OUTPUTS_DIR, f"{name}_music.mp4")

        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)

        audio = audio.subclip(0, video.duration)
        audio = audio.volumex(volume)

        final = video.set_audio(audio)
        final.write_videofile(output_path, codec="libx264")

        video.close()
        audio.close()
        return output_path

    @staticmethod
    def combine_videos(video_paths, output_path=None):
        """Combine multiple videos into one"""
        from moviepy.editor import VideoFileClip, concatenate_videoclips

        if output_path is None:
            output_path = os.path.join(OUTPUTS_DIR, "combined_ad.mp4")

        clips = [VideoFileClip(p) for p in video_paths]

        # Resize all to same size
        target_w = clips[0].w
        target_h = clips[0].h
        resized = [c.resize((target_w, target_h)) for c in clips]

        final = concatenate_videoclips(resized, method="compose")
        final.write_videofile(output_path, codec="libx264")

        for c in clips:
            c.close()

        return output_path

    @staticmethod
    def loop_video(video_path, loops=3, output_path=None):
        """Loop a video multiple times"""
        from moviepy.editor import VideoFileClip, concatenate_videoclips

        if output_path is None:
            name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(OUTPUTS_DIR, f"{name}_looped.mp4")

        clip = VideoFileClip(video_path)
        looped = concatenate_videoclips([clip] * loops)
        looped.write_videofile(output_path, codec="libx264")

        clip.close()
        return output_path

    @staticmethod
    def adjust_speed(video_path, speed=1.0, output_path=None):
        """Adjust video speed"""
        from moviepy.editor import VideoFileClip

        if output_path is None:
            name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(OUTPUTS_DIR, f"{name}_speed.mp4")

        clip = VideoFileClip(video_path)
        # `moviepy.editor` registers speedx() as a VideoClip method.
        final = clip.speedx(speed)
        final.write_videofile(output_path, codec="libx264")

        clip.close()
        return output_path
