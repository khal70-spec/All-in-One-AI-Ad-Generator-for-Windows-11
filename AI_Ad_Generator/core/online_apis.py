import os
import time
import requests
from config import ONLINE_PROVIDERS, USER_SETTINGS, OUTPUTS_DIR


class OnlineProvider:
    """Base class for cloud video-generation providers (Pika, Luma, ...)."""

    def __init__(self, provider_key):
        self.key = provider_key
        self.info = ONLINE_PROVIDERS[provider_key]
        self.name = self.info["name"]
        self.base_url = self.info["base_url"]

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _headers(self):
        api_key = USER_SETTINGS.get(f"{self.key}_api_key", "")
        if self.info["auth_scheme"] == "bearer":
            auth = f"Bearer {api_key}"
        else:
            auth = f"Key {api_key}"
        return {"Authorization": auth, "Content-Type": "application/json"}

    def is_configured(self):
        return bool(USER_SETTINGS.get(f"{self.key}_api_key", "").strip())

    def _post(self, path, payload):
        url = f"{self.base_url}{path}"
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=60)
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"{self.name} API error {resp.status_code}: {resp.text[:300]}"
            )
        return resp.json()

    def _get(self, path):
        url = f"{self.base_url}{path}"
        resp = requests.get(url, headers=self._headers(), timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(
                f"{self.name} API error {resp.status_code}: {resp.text[:300]}"
            )
        return resp.json()

    def _download(self, video_url):
        timestamp = int(time.time())
        output_path = os.path.join(OUTPUTS_DIR, f"online_{self.key}_{timestamp}.mp4")
        with requests.get(video_url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return output_path

    def _image_data_uri(self, path):
        """Read a local image and return a base64 data URI for API upload."""
        import base64
        import mimetypes
        mime = mimetypes.guess_type(path)[0] or "image/png"
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{b64}"

    # ------------------------------------------------------------------ #
    # To be implemented by subclasses
    # ------------------------------------------------------------------ #
    def _submit(self, prompt, image_path=None, webhook_url=None):
        raise NotImplementedError

    def _poll(self, job_id):
        """Return (done: bool, video_url: str|None, error: str|None)."""
        raise NotImplementedError

    def generate(self, prompt, image_path=None, webhook_url=None,
                 progress_callback=None, poll_timeout=360):
        if not self.is_configured():
            raise RuntimeError(
                f"{self.name} API key not configured. Add it in Settings → Online APIs."
            )

        job = self._submit(prompt, image_path=image_path, webhook_url=webhook_url)
        job_id = job.get("id") or job.get("generation_id")
        if not job_id:
            raise RuntimeError(f"{self.name}: no job id returned ({job})")

        if progress_callback:
            progress_callback(10, f"{self.name}: queued ({job_id})")

        deadline = time.time() + poll_timeout
        last_msg = ""
        while time.time() < deadline:
            done, video_url, error = self._poll(job_id)
            if error:
                raise RuntimeError(f"{self.name} failed: {error}")
            if done and video_url:
                if progress_callback:
                    progress_callback(90, f"{self.name}: downloading...")
                return self._download(video_url)
            # waiting
            if progress_callback and last_msg != "waiting":
                progress_callback(40, f"{self.name}: generating...")
                last_msg = "waiting"
            time.sleep(8)

        raise RuntimeError(f"{self.name}: timed out after {poll_timeout}s")


class PikaClient(OnlineProvider):
    """Pika Art video generation (https://pika.art)."""

    def _submit(self, prompt, image_path=None, webhook_url=None):
        payload = {
            "prompt": prompt,
            "aspect_ratio": "16:9",
        }
        if image_path:
            # Image-to-video: upload the source as a data URI.
            payload["image"] = self._image_data_uri(image_path)
        if webhook_url:
            payload["webhook_url"] = webhook_url
        return self._post("/video", payload)

    def _poll(self, job_id):
        data = self._get(f"/video/{job_id}")
        status = (data.get("status") or "").lower()
        if status == "failed":
            return True, None, data.get("error") or "generation failed"
        if status == "completed":
            url = (data.get("video") or {}).get("url") or data.get("url")
            if url:
                return True, url, None
        return False, None, None


class LumaClient(OnlineProvider):
    """Luma Dream Machine video generation (https://lumalabs.ai)."""

    def _submit(self, prompt, image_path=None, webhook_url=None):
        payload = {"prompt": prompt}
        if image_path:
            # Image-to-video: Luma expects an image URL / data URI.
            payload["image_url"] = self._image_data_uri(image_path)
        if webhook_url:
            payload["webhook_url"] = webhook_url
        return self._post("/generations", payload)

    def _poll(self, job_id):
        data = self._get(f"/generations/{job_id}")
        state = (data.get("state") or "").lower()
        if state == "failed":
            return True, None, data.get("failure_reason") or "generation failed"
        if state == "completed":
            assets = data.get("assets") or {}
            url = assets.get("video")
            if url:
                return True, url, None
        return False, None, None


def get_provider(provider_key):
    """Return a configured client instance for the given provider key."""
    if provider_key not in ONLINE_PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_key}")
    if provider_key == "pika":
        return PikaClient("pika")
    if provider_key == "luma":
        return LumaClient("luma")
    raise ValueError(f"Provider {provider_key} has no client implementation")
