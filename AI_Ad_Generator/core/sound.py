"""Audio for generated ads — fully offline / free.

Produces voiceovers with the OS text-to-speech engine (pyttsx3, which uses
Windows SAPI / espeak offline) and synthesizes a simple background music bed
with pydub (no files, no network). The result is muxed into the generated
video with moviepy. Every step degrades gracefully: if a component is
missing the video is simply returned unchanged.
"""

import os
from config import TEMP_DIR, OUTPUTS_DIR

# Point moviepy/pydub at the bundled ffmpeg so audio works without a system
# ffmpeg install. Safe to call early; it only sets things if available.
from .ffmpeg_setup import configure_ffmpeg
from .logger import get_logger
configure_ffmpeg()

log = get_logger("sound")


def generate_voiceover(text, output_path=None, rate=165):
    """Generate a voiceover .wav from ``text`` using offline TTS (pyttsx3)."""
    try:
        import pyttsx3
    except Exception:
        return None
    if not text or not text.strip():
        return None
    if output_path is None:
        output_path = os.path.join(TEMP_DIR, "voiceover.wav")
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        try:
            engine.setProperty("volume", 1.0)
        except Exception:
            pass
        engine.save_to_file(text, output_path)
        engine.runAndWait()
    except Exception as e:
        log.error("Voiceover error: %s", e)
        return None
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return output_path
    return None


def generate_background_music(output_path=None, duration=8, tempo=112):
    """Synthesize a short, royalty-free style music loop (.wav) with pydub."""
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine
    except Exception:
        return None
    if output_path is None:
        output_path = os.path.join(TEMP_DIR, "bgm.wav")
    try:
        # Pleasant major-pentatonic-ish arpeggio using sine oscillators.
        base = 220.0  # A3
        ratios = [1.0, 1.25, 1.5, 2.0, 1.5, 1.25]
        beat = int(60000 / tempo)  # ms per beat
        notes = []
        for i in range(int(duration * 1000 / beat) + 1):
            freq = base * ratios[i % len(ratios)]
            note = Sine(freq).to_audio_segment(duration=beat).apply_gain(-14)
            notes.append(note)
        music = sum(notes, AudioSegment.empty())[: duration * 1000]
        music.export(output_path, format="wav")
    except Exception as e:
        log.error("Background music error: %s", e)
        return None
    return output_path if os.path.exists(output_path) else None


def _loop_to_duration(audio_clip, duration):
    """Return an AudioClip looped/trimmed to ``duration`` seconds."""
    from moviepy.editor import concatenate_audioclips
    if audio_clip.duration >= duration:
        return audio_clip.subclip(0, duration)
    clips = []
    t = 0.0
    while t < duration:
        seg = audio_clip.subclip(0, min(audio_clip.duration, duration - t))
        clips.append(seg)
        t += seg.duration
    if len(clips) == 1:
        return clips[0]
    return concatenate_audioclips(clips)


def add_sound_to_video(video_path, prompt=None, voiceover=True, music=True,
                       music_volume=0.35):
    """Return a copy of ``video_path`` with sound (voiceover and/or music).

    On any failure the original ``video_path`` is returned unchanged.
    """
    if not (voiceover or music):
        return video_path

    from moviepy.editor import (VideoFileClip, AudioFileClip,
                                 CompositeAudioClip, concatenate_audioclips)

    try:
        video = VideoFileClip(video_path)
        dur = video.duration
        audio_clips = []

        if voiceover and prompt:
            vp = generate_voiceover(prompt)
            if vp:
                a = AudioFileClip(vp)
                a = _loop_to_duration(a, dur).volumex(1.0)
                audio_clips.append(a)

        if music:
            mp = generate_background_music(duration=int(dur) + 1)
            if mp:
                a = AudioFileClip(mp)
                a = _loop_to_duration(a, dur).volumex(music_volume)
                audio_clips.append(a)

        if not audio_clips:
            video.close()
            return video_path

        final_audio = audio_clips[0] if len(audio_clips) == 1 \
            else CompositeAudioClip(audio_clips)
        out = os.path.join(
            OUTPUTS_DIR,
            f"{os.path.splitext(os.path.basename(video_path))[0]}_sound.mp4")
        final = video.set_audio(final_audio)
        final.write_videofile(out, codec="libx264", audio_codec="aac")
        video.close()
        for a in audio_clips:
            try:
                a.close()
            except Exception:
                pass
        return out if os.path.exists(out) else video_path
    except Exception as e:
        log.error("add_sound_to_video error: %s", e)
        return video_path
