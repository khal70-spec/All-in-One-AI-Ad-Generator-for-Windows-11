# 🎬 Tutorial Video Script — All-in-One AI Ad Generator

> A ready-to-record script for a YouTube / social walkthrough of the app.
> Everything shown uses **free, open-source or free-tier** tooling:
> the app itself, open models (ZeroScope, ModelScope, SDXL, SVD, AnimateDiff,
> Mochi, HunyuanVideo, LTX-Video), free-tier cloud APIs (Pika/Luma),
> and free record/edit tools (OBS Studio, CapCut, DaVinci Resolve Free).

**Video length target:** ~8–10 minutes
**Recording tool:** OBS Studio (free) — capture the app window at 1920×1080
**Voiceover:** any free TTS or your own mic
**Editing:** CapCut / DaVinci Resolve Free (both free)

---

## Scene 0 — Intro (0:00–0:30)

| Element | Content |
|--------|---------|
| **Visual** | App logo (`assets/logo.png`) + title card: *“Make Pro Product Ads with AI — 100% Free, On Your PC”* |
| **Narration** | “In this video I’ll show you how to turn a product photo or a single sentence into a polished, ready-to-post video ad — using a free, open-source Windows app and completely free AI models. No monthly subscription, no watermark.” |
| **On-screen** | Subscribe / Like badge · Chapter markers |

---

## Scene 1 — What the app does (0:30–1:15)

| Element | Content |
|--------|---------|
| **Visual** | Quick cuts of each tab: Text→Video, Image→Video, Prompt Generator, Batch, Video Editor, Settings, Online APIs. |
| **Narration** | “The All-in-One AI Ad Generator has six tabs. Text-to-Video turns a sentence into clips with models like ZeroScope and ModelScope. Image-to-Video animates a product photo with Stable Video Diffusion or AnimateDiff. There’s a Prompt Generator, a Batch mode for many products at once, a Video Editor, and a Settings tab to download models and plug in free cloud APIs like Pika and Luma.” |
| **On-screen** | Tab highlights + quick captions |

---

## Scene 2 — Install (1:15–2:15)

| Element | Content |
|--------|---------|
| **Visual** | File Explorer showing `install.bat`, double-click → terminal installing venv + PyTorch + deps. Then `start.bat`. |
| **Narration** | “Installation is one double-click. Run `install.bat` — it creates a Python virtual environment, installs PyTorch with CUDA for your NVIDIA GPU, and all dependencies. Then run `start.bat` to launch. No coding required.” |
| **On-screen** | Annotation: “Python 3.10+ with ‘Add to PATH’ • NVIDIA GPU recommended (works on CPU too)” |
| **Free tool** | The app + `install.bat` (MIT-style, free) |

---

## Scene 3 — Download models (2:15–3:00)

| Element | Content |
|--------|---------|
| **Visual** | Settings → Model Manager. Click **Download** on ZeroScope, Stable Video Diffusion, Stable Diffusion XL. |
| **Narration** | “Head to Settings, open Model Manager, and download the models you want. These are downloaded once and stored locally — they’re free open-source weights. Start with ZeroScope and Stable Video Diffusion; add SDXL if you want to generate product images from text, and Mochi / HunyuanVideo / LTX-Video if you have a bigger GPU.” |
| **On-screen** | Progress bar fills · “Stored in models/” |

---

## Scene 4 — Prompt Generator (3:00–3:45)

| Element | Content |
|--------|---------|
| **Visual** | Prompt tab: type “Wireless earbuds”, pick style *cinematic*, click **Generate Prompts**. Show batch variations. |
| **Narration** | “Great ads start with great prompts. Type your product, pick a style — cinematic, luxury, tech — and the Prompt Generator writes an optimized prompt plus a negative prompt. Hit ‘Generate Multiple Variations’ to get a whole batch you can copy.” |
| **On-screen** | Copy All button highlight |

---

## Scene 5 — Text to Video (3:45–5:00)

| Element | Content |
|--------|---------|
| **Visual** | Text→Video tab: paste a generated prompt, pick template *Product Showcase*, set Steps/Guidance/Frames, model = ZeroScope, click **GENERATE VIDEO**. Show preview + `outputs/`. |
| **Narration** | “Now the fun part. Paste your prompt, choose an ad template, tweak steps and frames, and hit Generate. In a minute or two you have a 512p clip saved to the outputs folder. Try ModelScope for a different look, or Mochi / HunyuanVideo / LTX-Video on a stronger GPU for higher quality.” |
| **On-screen** | Settings used: Steps 25–30, Guidance 7.5, Frames 24 |

---

## Scene 6 — Image to Video + SDXL (5:00–6:15)

| Element | Content |
|--------|---------|
| **Visual** | Image→Video tab: click **Generate Image (SDXL)** with prompt “red sneaker on marble”; then enable Remove Background + Enhance + Upscale, click **ANIMATE IMAGE** (model SVD). |
| **Narration** | “No product photo? Click ‘Generate Image’ to create one with Stable Diffusion XL. Then select it, turn on background removal, enhancement, and even a free online upscale for extra crispness, and animate it with Stable Video Diffusion or AnimateDiff. You can also pick ‘online (Pika/Luma)’ to animate via the cloud if you have no GPU.” |
| **On-screen** | Before/after background removal |

---

## Scene 7 — Batch mode (6:15–7:00)

| Element | Content |
|--------|---------|
| **Visual** | Batch tab: paste 5 products, mode = Products→Video, click **GENERATE ALL**. Show progress + log + stop button. |
| **Narration** | “Need a whole ad set? The Batch tab queues every product and renders them one after another — text-to-video, image-to-video, image generation, or even cloud generation through Pika and Luma. Watch the live log, and stop anytime.” |
| **On-screen** | “5 jobs queued → 5 mp4s in outputs/” |

---

## Scene 8 — Video Editor (7:00–7:45)

| Element | Content |
|--------|---------|
| **Visual** | Editor tab: select a clip, add text overlay “50% OFF”, add background music, combine two clips, loop, change speed. |
| **Narration** | “Finish in the Editor: drop in a text overlay, add royalty-free music, combine multiple clips into one ad, loop it, or speed it up. Everything exports back to outputs as an mp4.” |
| **On-screen** | “Use free music from Pixabay / YouTube Audio Library” |

---

## Scene 9 — Online APIs + Webhooks (7:45–8:30)

| Element | Content |
|--------|---------|
| **Visual** | Settings → Online APIs: paste Pika key, Save. Settings → Webhook Receiver: Start on port 8000, copy URL. Then Batch → Online Video submits with webhook_url. |
| **Narration** | “If you don’t have a GPU, the app talks to free-tier cloud APIs. Add your Pika or Luma key in Settings, start the built-in Webhook Receiver to catch completion callbacks, and generate in the cloud. Keys are stored locally in config.json.” |
| **On-screen** | “Keys stay on your machine • ngrok for public webhook URL” |

---

## Scene 10 — Outro (8:30–9:00)

| Element | Content |
|--------|---------|
| **Visual** | Montage of generated ads + repo link. |
| **Narration** | “That’s it — from a sentence or a photo to a finished ad, entirely with free tools. Grab the app from the repo, hit like if this helped, and I’ll see you in the next one.” |
| **On-screen** | Repo URL · “Made with free open-source AI” |

---

## ✅ Free-tool checklist (for the description)

- **App:** All-in-One AI Ad Generator (open source)
- **Models:** ZeroScope, ModelScope, SDXL, SVD, AnimateDiff, Mochi, HunyuanVideo, LTX-Video (all free/open weights)
- **Cloud (optional):** Pika & Luma free tiers
- **Record:** OBS Studio (free)
- **Edit:** CapCut or DaVinci Resolve Free
- **Music:** Pixabay / YouTube Audio Library (royalty-free)

## 🎨 Thumbnail idea
Split screen: left = plain product photo, right = animated AI ad, big text
**“Turn Photos into Ads — FREE”**, red/coral accent matching the app theme.
