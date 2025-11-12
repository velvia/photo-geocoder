# Setup Guide for New Users

## One-Time System Setup

### 1. Install uv (Python package manager)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Add uv to your PATH

**For Fish shell** (add to `~/.config/fish/config.fish`):
```fish
set -gx PATH "$HOME/.local/bin" $PATH
```

**For Bash/Zsh** (add to `~/.bashrc` or `~/.zshrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then reload your shell:
```bash
source ~/.config/fish/config.fish  # Fish
# or
source ~/.bashrc                    # Bash
```

## Project Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd photo-geocoder
```

### 2. Create virtual environment and install dependencies
```bash
# Create venv
uv venv

# Activate it
source .venv/bin/activate.fish  # Fish
# or
source .venv/bin/activate       # Bash/Zsh

# Install all dependencies
uv pip install -r requirements.txt
```

### 3. Install Playwright browsers (for Instagram script only)
```bash
playwright install webkit chromium
```

## Quick Test

### Test Photo Geocoder
```bash
python photo-geocoder.py --help
```

### Test Instagram Hashtag Search
```bash
python instagram-hashtag-search.py --help
```

## Usage Examples

### Photo Geocoder
```bash
python photo-geocoder.py /path/to/your/photos
```

### Instagram Search
```bash
# Search a few users
python instagram-hashtag-search.py --hashtag rebelscapes --users alice bob

# Use a file with usernames
python instagram-hashtag-search.py --hashtag rebelscapes --users-file users.txt

# Use Safari
python instagram-hashtag-search.py --hashtag rebelscapes --users alice --browser webkit
```

## Troubleshooting

### "uv: command not found"
Make sure you've added `$HOME/.local/bin` to your PATH and reloaded your shell.

### "playwright: command not found"
Make sure you've activated the virtual environment:
```bash
source .venv/bin/activate.fish
```

### Instagram script not working
- Make sure Playwright browsers are installed: `playwright install webkit chromium`
- Try logging into Instagram in the browser window that opens
- Increase wait time with `--wait 5` if you're being rate limited

### Photo Geocoder "exiftool not found"
Install exiftool:
```bash
brew install exiftool  # macOS with Homebrew
```

## Updating Dependencies

To add a new package:
```bash
# Add to requirements.txt manually, then:
uv pip install -r requirements.txt

# Or install directly:
uv pip install package-name

# Then update requirements.txt:
uv pip freeze > requirements.txt
```

## Alternative: Using pyproject.toml

If you prefer to use pyproject.toml instead of requirements.txt:
```bash
uv pip install -e .
```

This installs the project in editable mode with all dependencies from pyproject.toml.

