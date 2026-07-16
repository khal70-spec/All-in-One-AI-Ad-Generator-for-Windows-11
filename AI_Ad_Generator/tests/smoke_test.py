#!/usr/bin/env python3
"""Offline smoke tests for the AI Ad Generator.

These run WITHOUT a GPU, torch, diffusers or a display: heavy dependencies
are stubbed out so pure logic can be verified. Run from the app folder:

    cd AI_Ad_Generator
    python tests/smoke_test.py

Requires only: Pillow, requests, psutil, numpy (all in requirements.txt,
plus `imageio`+`imageio-ffmpeg` for the optional video-sidecar test).
"""

import json
import os
import sys
import types

# Make the app importable no matter where we are launched from.
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

FAILED = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except Exception as e:  # noqa: BLE001 - test harness
        FAILED.append((name, e))
        print(f"FAIL  {name}: {e}")


# --------------------------------------------------------------------- #
# Stub heavy third-party modules so pure logic can be imported offline.
# --------------------------------------------------------------------- #
def stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


torch = stub("torch")
torch.cuda = types.SimpleNamespace(
    is_available=lambda: False,
    get_device_name=lambda i: "None",
    get_device_properties=lambda i: types.SimpleNamespace(total_memory=0),
    empty_cache=lambda: None,
)
torch.float16 = "float16"
torch.float32 = "float32"
torch.bfloat16 = "bf16"
torch.Generator = lambda device="cpu": types.SimpleNamespace(
    manual_seed=lambda s: None)
stub("huggingface_hub", snapshot_download=lambda **kw: "/tmp/fake")


# --------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------- #
def test_config_settings_roundtrip():
    import config
    assert os.path.isdir(config.MODELS_DIR)
    config.USER_SETTINGS["pika_api_key"] = "test123"
    config.save_settings()
    config.USER_SETTINGS["pika_api_key"] = ""
    config.load_settings()
    assert config.USER_SETTINGS["pika_api_key"] == "test123"
    os.remove(config.CONFIG_FILE)
    config.USER_SETTINGS["pika_api_key"] = ""


def test_ui_prefs():
    import config
    config.set_ui_pref("smoke", "steps", 33)
    assert config.get_ui_pref("smoke", "steps") == 33
    assert config.get_ui_pref("smoke", "missing", 7) == 7
    config.USER_SETTINGS["ui_prefs"].pop("smoke", None)
    if os.path.exists(config.CONFIG_FILE):
        os.remove(config.CONFIG_FILE)


def test_prompt_generator():
    from core.prompt_generator import PromptGenerator
    pg = PromptGenerator()
    p = pg.generate_prompt("Test Watch", style="luxury",
                           custom_details="gold strap")
    assert "Test Watch" in p and "gold strap" in p
    assert len(pg.generate_batch_prompts("X", count=3)) == 3
    assert "blurry" in pg.generate_negative_prompt()


def test_model_manager():
    from core.model_manager import ModelManager, ESTIMATED_MODEL_SIZES_GB
    mm = ModelManager()
    info = mm.get_system_info()
    assert info["device"] == "cpu" and "available_models" in info
    assert mm.check_vram_fit("mochi") is None  # CPU mode -> no VRAM warning
    assert ESTIMATED_MODEL_SIZES_GB["mochi"] >= 24
    try:
        mm.download_model("nonexistent_model")
        raise AssertionError("should have raised")
    except ValueError:
        pass


def test_progress_and_cancel():
    from core.progress import make_step_kwargs, GenerationCancelled
    calls = []

    class FakePipeOld:
        def __call__(self, callback=None, callback_steps=None):
            pass

    class FakePipeNew:
        def __call__(self, callback_on_step_end=None):
            pass

    kw = make_step_kwargs(FakePipeOld(), 10,
                          lambda v, m: calls.append((v, m)))
    assert "callback" in kw and kw["callback_steps"] == 1
    kw["callback"](1, None, None)

    kw2 = make_step_kwargs(FakePipeNew(), 10,
                           lambda v, m: calls.append((v, m)))
    kw2["callback_on_step_end"](None, 4, 0.5, {})
    assert calls, "progress callbacks not firing"

    # cancel_check must raise inside callbacks
    kw3 = make_step_kwargs(FakePipeNew(), 10, None,
                           cancel_check=lambda: True)
    try:
        kw3["callback_on_step_end"](None, 0, 0.5, {})
        raise AssertionError("should have raised GenerationCancelled")
    except GenerationCancelled:
        pass


class _Args:  # small helper for signature checks
    pass


def test_video_editor_api():
    import inspect
    from core.video_editor import VideoEditor
    for meth, args in [("add_text_to_video", ("video_path", "text")),
                       ("add_music", ("video_path", "audio_path")),
                       ("combine_videos", ("video_paths",)),
                       ("loop_video", ("video_path",)),
                       ("adjust_speed", ("video_path",))]:
        sig = inspect.signature(getattr(VideoEditor, meth))
        for a in args:
            assert a in sig.parameters, f"{meth} missing {a}"


def test_utils():
    from core.utils import human_size, safe_slug, open_path
    assert human_size(0) == "0 B"
    assert human_size(1024**3) == "1.0 GB"
    assert safe_slug("Hello, World! 2024") == "hello_world_2024"
    assert open_path("/definitely/not/here.xyz") is False


def test_logger():
    from core.logger import get_logger, _LOG_FILE
    log = get_logger("smoke")
    log.info("smoke test entry")
    for h in log.handlers:
        h.flush()
    assert os.path.exists(_LOG_FILE)


def test_ffmpeg_and_sound():
    from core.ffmpeg_setup import configure_ffmpeg
    configure_ffmpeg()  # must not raise even without imageio-ffmpeg
    import core.sound as sound
    assert callable(sound.add_sound_to_video)


def test_webhook_server():
    import time
    import urllib.request
    from core.webhook_server import WebhookReceiver
    logs = []
    recv = WebhookReceiver(port=8399, log_callback=logs.append)
    recv.start()
    time.sleep(0.3)
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8399/", data=b'{"state":"completed"}',
            headers={"Content-Type": "application/json"})
        assert urllib.request.urlopen(req, timeout=5).status == 200
        time.sleep(0.3)
        assert any("Webhook received" in line for line in logs)
    finally:
        recv.stop()


def test_online_apis():
    import config
    from core.online_apis import get_provider
    pk = get_provider("pika")
    assert pk.info["auth_scheme"] == "key"
    config.USER_SETTINGS["pika_api_key"] = "abc"
    assert pk.is_configured()
    config.USER_SETTINGS["pika_api_key"] = ""
    assert not pk.is_configured()
    try:
        get_provider("bogus")
        raise AssertionError("should have raised")
    except ValueError:
        pass


def test_unknown_models_rejected():
    from core.model_manager import ModelManager
    from core.text_to_video import TextToVideoGenerator
    from core.image_to_video import ImageToVideoGenerator
    from core.text_to_image import TextToImageGenerator
    mm = ModelManager()
    for call in (lambda: TextToVideoGenerator(mm).generate(
                     prompt="x", model="bogus"),
                 lambda: ImageToVideoGenerator(mm).generate_from_image(
                     "/tmp/none.png", model="bogus"),
                 lambda: TextToImageGenerator(mm).generate(
                     prompt="x", model="bogus")):
        try:
            call()
            raise AssertionError("unknown model should raise")
        except (ValueError, RuntimeError):
            pass


def test_image_editor():
    import tempfile
    from PIL import Image
    from core.image_editor import ImageEditor
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "src.png")
        Image.new("RGB", (300, 200), (10, 120, 220)).save(src)
        assert Image.open(ImageEditor.resize_image(
            src, 128, 64, os.path.join(d, "r.png"))).size == (128, 64)
        assert os.path.exists(ImageEditor.add_text_overlay(
            src, "SALE", output_path=os.path.join(d, "t.png")))
        assert os.path.exists(ImageEditor.enhance_image(
            src, brightness=1.2, output_path=os.path.join(d, "e.png")))
        assert Image.open(ImageEditor.create_product_composite(
            src, size=(256, 256), output_path=os.path.join(d, "c.png"))
        ).size == (256, 256)


def test_upscaler_validation():
    from core.upscaler import UpscalerClient
    try:
        UpscalerClient().upscale_image("/tmp/definitely-not-here.png")
        raise AssertionError("should have raised")
    except RuntimeError:
        pass


def test_video_sidecar_metadata():
    """_save_video writes a JSON sidecar with generation params."""
    try:
        import numpy as np  # noqa: F401
        import imageio  # noqa: F401
        import imageio_ffmpeg  # noqa: F401
    except ImportError:
        print("      (skipped: numpy/imageio/imageio-ffmpeg not installed)")
        return
    import numpy as np
    from core.model_manager import ModelManager
    from core.text_to_video import TextToVideoGenerator
    gen = TextToVideoGenerator(ModelManager())
    frames = [np.zeros((64, 64, 3), dtype=np.uint8) for _ in range(4)]
    out = gen._save_video(frames, 1234, meta={"prompt": "x", "seed": 1234})
    try:
        assert os.path.exists(out)
        with open(out + ".json", encoding="utf-8") as f:
            meta = json.load(f)
        assert meta["prompt"] == "x" and meta["seed"] == 1234
        assert "created" in meta
    finally:
        for p in (out, out + ".json"):
            if os.path.exists(p):
                os.remove(p)


def test_batch_summary():
    import json as _json
    from core.model_manager import ModelManager
    from core.batch import BatchProcessor
    bp = BatchProcessor(ModelManager())
    results = [{"job": {"type": "text"}, "output": "/tmp/a.mp4",
                "status": "ok"},
               {"job": {"type": "image"}, "output": None,
                "status": "error", "error": "boom"}]
    path = bp._write_summary(results)
    assert path and os.path.exists(path)
    with open(path, encoding="utf-8") as f:
        data = _json.load(f)
    assert data["succeeded"] == 1 and data["failed"] == 1
    os.remove(path)


def main():
    tests = [
        ("config settings round-trip", test_config_settings_roundtrip),
        ("ui prefs persistence", test_ui_prefs),
        ("prompt generator", test_prompt_generator),
        ("model manager", test_model_manager),
        ("progress + cancel token", test_progress_and_cancel),
        ("video editor API", test_video_editor_api),
        ("utils (human_size/open_path)", test_utils),
        ("logger", test_logger),
        ("ffmpeg setup + sound module", test_ffmpeg_and_sound),
        ("webhook server", test_webhook_server),
        ("online apis", test_online_apis),
        ("unknown models rejected", test_unknown_models_rejected),
        ("image editor", test_image_editor),
        ("upscaler validation", test_upscaler_validation),
        ("video metadata sidecar", test_video_sidecar_metadata),
        ("batch run summary", test_batch_summary),
    ]
    for name, fn in tests:
        check(name, fn)

    print()
    if FAILED:
        print(f"{len(FAILED)} test(s) FAILED")
        sys.exit(1)
    print("ALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
