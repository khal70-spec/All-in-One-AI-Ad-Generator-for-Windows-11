# Troubleshooting Guide

## Installation Issues

### Python not found

**Error**: `'python' is not recognized as an internal or external command`

**Solution**:
1. Install Python 3.10+ from https://python.org
2. **Important**: During installation, check "Add Python to PATH"
3. Restart your terminal and try again

### Virtual environment creation fails

**Error**: `Error: The virtual environment was not created successfully`

**Solution**:
```bash
# Try installing virtualenv separately
pip install --user virtualenv
virtualenv venv
venv\Scripts\activate.bat
```

### CUDA not detected

**Error**: `No CUDA GPU detected - running on CPU (slower)`

**Solution**:
1. Check if you have an NVIDIA GPU: `nvidia-smi`
2. If no output, your system doesn't have an NVIDIA GPU
3. Install NVIDIA drivers from https://nvidia.com/download/driverDetails.aspx
4. Reinstall PyTorch with CUDA support:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

## Runtime Issues

### Out of Memory Error

**Error**: `RuntimeError: CUDA out of memory`

**Solutions** (in order of effectiveness):
1. Close other GPU applications (Chrome, Discord, etc.)
2. Reduce video dimensions (512x512 → 256x256)
3. Reduce number of frames (25 → 16)
4. Reduce diffusion steps (25 → 15)
5. Use a lighter model:
   - **Lighter**: ZeroScope, SVD (8GB)
   - **Medium**: CogVideoX (16GB), SDXL (8GB)
   - **Heavier**: Mochi, HunyuanVideo (24GB), LTX-Video (12GB)

### Generation stuck/frozen

**Error**: "No progress after 5 minutes"

**Solutions**:
1. Click the **Cancel (⏹)** button - it stops cleanly
2. Check `temp/app.log` for error messages
3. Close the app and check GPU memory: `nvidia-smi`
4. If GPU stuck, restart your computer

### Model download fails

**Error**: `ConnectionError`, `FileNotFoundError`, `HTTPError`

**Solutions**:
1. Check internet connection
2. Verify you have **at least 10GB free disk space**
3. Check firewall isn't blocking downloads
4. Try downloading individual models:
   - Open **Settings & Models** tab
   - Click download for specific model
   - Check the console for download progress

### Video file corrupted/won't play

**Error**: `[CODEC] unsupported codec`, `File is not a valid video`

**Solutions**:
1. Install ffmpeg: https://ffmpeg.org/download.html
2. Ensure ffmpeg is in PATH
3. Check `temp/app.log` for encoding errors
4. Try different video player (VLC, Media Player Classic)

## Performance Issues

### Very slow generation

**Expected times** (per model, 25 steps, 24 frames):
- **GPU (8GB)**: 2-5 minutes
- **GPU (16GB)**: 1-3 minutes  
- **CPU**: 30+ minutes

**To improve**:
1. Reduce quality settings (fewer steps, fewer frames)
2. Close background applications
3. Check GPU isn't overheating: `nvidia-smi -q -d TEMPERATURE`
4. Update GPU drivers

### High memory usage (even idle)

**Solution**: Models stay in memory for faster generation of multiple videos. To free memory:
1. Go to **Settings & Models**
2. Find loaded models (will say "Loaded")
3. Click "Unload" next to each
4. Or restart the application

## UI Issues

### Window won't open/appears blank

**Error**: Window opens but is blank/freezes

**Solution**:
1. Delete config file: `AI_Ad_Generator/config.json`
2. Restart the application
3. If still broken, check graphics drivers:
   - Update GPU drivers
   - Update CustomTkinter: `pip install --upgrade customtkinter`

### Text/buttons look blurry or wrong size

**Solution**:
1. Edit `ui/styles.py`
2. Adjust font sizes or DPI settings
3. Restart the app

### Keyboard input doesn't work

**Solution**:
1. Click in the text field first (to focus it)
2. If still doesn't work, update CustomTkinter:
   ```bash
   pip install --upgrade customtkinter
   ```

## API/Online Issues

### Pika/Luma API errors

**Error**: `401 Unauthorized`, `Invalid API key`

**Solutions**:
1. Verify API key is correct (no extra spaces)
2. Check key is still valid on provider's website
3. Generate new key if needed
4. Clear settings: Delete `AI_Ad_Generator/config.json`

### Webhook server won't start

**Error**: `Port already in use`, `Permission denied`

**Solutions**:
1. Change port in settings
2. Or restart computer to free ports
3. Disable other webhook servers

## Logging & Debugging

### Where are the logs?

Open: `AI_Ad_Generator/temp/app.log`

**What to check**:
1. Timestamp of error
2. Module name in brackets (e.g., `[t2v]`)
3. Error message and stack trace

### Enable debug logging

1. Edit `core/logger.py`
2. Change level from `INFO` to `DEBUG`
3. Restart app
4. Check `temp/app.log` for detailed info

### Submit a bug report

Include:
1. Your `temp/app.log` (last 50 lines around error)
2. GPU info: `nvidia-smi`
3. Python version: `python --version`
4. **Exact steps** to reproduce
5. What you expected vs. what happened

## Advanced Troubleshooting

### Run offline smoke tests

No GPU/internet needed:
```bash
cd AI_Ad_Generator
python tests\smoke_test.py
```

### Check disk space

Models need **25-50GB** depending on which ones you download:
```bash
# Check free space
dir C:\  # Shows C: drive
```

### Reset to defaults

```bash
# Delete config and cached models
del AI_Ad_Generator\config.json
rmdir /s AI_Ad_Generator\models\  # Delete downloaded models
rmdir /s AI_Ad_Generator\temp\    # Clear temp files

# Restart app
start.bat
```

### Collect diagnostics

Create a debug report:
```python
import torch
import os
from core.model_manager import ModelManager

mm = ModelManager()
print("System Info:", mm.get_system_info())
print("Available VRAM:", mm.available_vram_gb)
print("Disk Space Check:", mm.check_disk_space('outputs'))
print("Config Dir:", os.path.exists('config.json'))
```

## Still Having Issues?

1. **Check FAQ**: Common issues answered
2. **Search Issues**: GitHub issue tracker
3. **Ask Community**: Create new issue with `help wanted` label
4. **Read Docs**: Check `docs/` folder

## Common Solutions Quick Reference

| Issue | Quick Fix |
|-------|----------|
| "No GPU detected" | Install CUDA drivers, reinstall PyTorch |
| "Out of memory" | Reduce dimensions/frames, pick lighter model |
| "Can't download model" | Check internet, free disk space (10GB+) |
| "Video won't play" | Install ffmpeg, try VLC player |
| "App won't start" | Delete `config.json`, update CustomTkinter |
| "Generation stuck" | Click Cancel, check GPU with `nvidia-smi` |
| "Corrupted log file" | Delete `temp/app.log`, restart app |

---

**Still stuck?** Open an issue with your `temp/app.log` and we'll help! 🆘
