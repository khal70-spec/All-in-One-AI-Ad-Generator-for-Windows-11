# Contributing to AI Ad Generator

Thank you for your interest in contributing to the AI Ad Generator! This guide will help you get started.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/All-in-One-AI-Ad-Generator-for-Windows-11.git
   cd All-in-One-AI-Ad-Generator-for-Windows-11
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate.bat

# Install development dependencies
pip install -r AI_Ad_Generator/requirements.txt
```

## Running Tests

```bash
# Run smoke tests (no GPU required)
python AI_Ad_Generator/tests/smoke_test.py

# Run comprehensive tests
python AI_Ad_Generator/tests/comprehensive_test.py
```

## Code Style

- Use **type hints** for all function parameters and returns
- Add **docstrings** to all functions and classes
- Follow **PEP 8** naming conventions
- Limit lines to **100 characters** where possible
- Use **meaningful variable names**

### Example:

```python
from typing import Optional, Dict, Any

def process_video(input_path: str, num_frames: int = 24) -> Dict[str, Any]:
    """Process a video file.
    
    Args:
        input_path: Path to input video file
        num_frames: Number of frames to extract
        
    Returns:
        Dictionary with processing results
        
    Raises:
        FileNotFoundError: If input file doesn't exist
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Video not found: {input_path}")
    # Implementation...
```

## Error Handling

- Always validate inputs before processing
- Use specific exception types (not generic `Exception`)
- Log errors with appropriate levels (warning, error, critical)
- Provide meaningful error messages to users

```python
try:
    image = Image.open(image_path)
except FileNotFoundError:
    raise FileNotFoundError(f"Image not found: {image_path}")
except Exception as e:
    log.error("Failed to load image: %s", e)
    raise IOError(f"Failed to process image: {str(e)}")
```

## Memory Management

- Always clean up resources (close files, free VRAM)
- Use context managers (`with` statements) where possible
- Call `torch.cuda.empty_cache()` after heavy GPU operations
- Test with memory profilers when adding new features

## Testing

- Write tests for new functionality
- Test edge cases and error conditions
- Ensure backward compatibility
- Test on both CPU and GPU if possible

## Pull Request Process

1. **Update** tests and documentation
2. **Run** tests locally:
   ```bash
   python AI_Ad_Generator/tests/smoke_test.py
   python AI_Ad_Generator/tests/comprehensive_test.py
   ```
3. **Commit** with clear messages:
   ```bash
   git commit -m "feat: add new feature description"
   ```
4. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Create Pull Request** on GitHub with:
   - Clear description of changes
   - Reference to any related issues
   - Screenshots/videos if UI-related

## Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

### Types:
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring
- `docs:` - Documentation
- `test:` - Test additions/changes
- `chore:` - Maintenance tasks

### Example:
```
feat: add VRAM monitoring to model manager

Add real-time VRAM usage tracking and warnings when
VRAM usage approaches GPU memory limits.

Fixes #123
```

## Reporting Issues

When reporting bugs, please include:

1. **Python version**: `python --version`
2. **GPU info**: `nvidia-smi` output
3. **Error message**: Full traceback from `temp/app.log`
4. **Steps to reproduce**: Exact steps to trigger the issue
5. **Expected vs actual**: What should happen vs what does happen

## Feature Requests

Before requesting a feature:

1. Check existing issues/PRs
2. Describe the use case clearly
3. Provide examples if possible
4. Consider performance implications

## Questions?

Feel free to:
- Open an issue with the `question` label
- Check existing issues for similar questions
- Review documentation in `docs/`

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing! 🎉
