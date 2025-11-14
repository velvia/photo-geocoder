# photo-geocoder

A collection of Python scripts for working with photos and Instagram data.

## 📦 Scripts

### 1. `photo-geocoder.py`
Appends geocoded city names to your photos in a folder using EXIF GPS data.

### 2. `photo-denoise-ai.py`
AI-powered photo denoising script.

### 3. `instagram-hashtag-search.py`
Searches Instagram hashtags and finds the most recent posting date for each user. Uses Playwright for browser automation to search hashtags like `#rebelscapes_username`.

## 🚀 Quick Setup with uv (Recommended)

### Install uv (one-time setup)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Add to your Fish shell config (`~/.config/fish/config.fish`):
```fish
set -gx PATH "$HOME/.local/bin" $PATH
```

Then reload: `source ~/.config/fish/config.fish`

### Install Dependencies

**Option A - Using pyproject.toml:**
```bash
cd photo-geocoder
uv venv
source .venv/bin/activate.fish  # or .venv/bin/activate for bash
uv pip install -e .
```

**Option B - Using requirements.txt:**
```bash
cd photo-geocoder
uv venv
source .venv/bin/activate.fish
uv pip install -r requirements.txt
```

### Install Playwright Browsers (for Instagram script)
```bash
playwright install webkit chromium
```

## 📖 Usage

### Photo Geocoder
```bash
python photo-geocoder.py /path/to/photos
```

### Instagram Hashtag Search

**Search for multiple users:**
```bash
python instagram-hashtag-search.py --hashtag rebelscapes --users alice bob charlie
```

**Use a file with usernames:**
```bash
python instagram-hashtag-search.py --hashtag rebelscapes --users-file users.txt
```

**Use Safari (webkit) instead of Chrome:**
```bash
python instagram-hashtag-search.py --hashtag rebelscapes --users alice --browser webkit
```

**Run in headless mode:**
```bash
python instagram-hashtag-search.py --hashtag rebelscapes --users alice --headless
```

**Custom output file:**
```bash
python instagram-hashtag-search.py --hashtag rebelscapes --users alice -o results.json
```

**Give yourself more time to log in (60 seconds):**
```bash
python instagram-hashtag-search.py --hashtag rebelscapes --users alice --login-wait 60
```

**Check more posts (default is 12):**
```bash
python instagram-hashtag-search.py --hashtag rebelscapes --users alice --max-posts 20
```

**Save your login session (RECOMMENDED - Fast & Easy!):**
```bash
# First time - log in and save session
python instagram-hashtag-search.py --hashtag rebelscapes --users alice --save-session --login-wait 60

# Every time after - automatically uses saved login!
python instagram-hashtag-search.py --hashtag rebelscapes --users alice --save-session
```

**See all options:**
```bash
python instagram-hashtag-search.py --help
```

## 📋 Instagram Search Features

- ✅ Searches Instagram hashtags like `#rebelscapes_username`
- ✅ **Checks multiple posts** to find the actual most recent date (default: 12 posts)
- ✅ Clicks through each post, extracts dates, and determines the newest one
- ✅ **Saves your login session** - log in once, stays logged in forever! (use `--save-session`)
- ✅ Supports multiple browsers (Chrome/Chromium, Safari/WebKit, Firefox)
- ✅ Can read usernames from a file (one per line)
- ✅ Saves results to JSON with detailed stats
- ✅ Shows progress and summary
- ✅ Handles errors gracefully
- ✅ Respects rate limiting with configurable wait times

## 📝 Output Format (Instagram Search)

Results are saved as JSON:

```json
{
  "alice": {
    "username": "alice",
    "hashtag": "#rebelscapes_alice",
    "post_count": "42 posts",
    "most_recent_date": "2025-11-10 15:30:00",
    "status": "success"
  },
  "bob": {
    "username": "bob",
    "hashtag": "#rebelscapes_bob",
    "post_count": 0,
    "most_recent_date": null,
    "status": "no_posts"
  }
}
```

## ⚠️ Important Notes

### Instagram Search
- **Login Options:**
  - **Option A (RECOMMENDED):** Use `--save-session` to save your login. Log in once on first run, then never again!
  - **Option B:** Log in each time the script runs (use `--login-wait 60` for 60 seconds to log in)
- **Session Storage:** Cookies and login info are saved to `.instagram-session/` directory (ignored by git)
- **Post Checking:** By default checks 12 posts per hashtag. Instagram doesn't sort chronologically, so checking multiple posts finds the actual newest one
- Use `--max-posts 20` to check more posts (higher = slower but more accurate)
- Instagram may rate limit if you search too many hashtags too quickly (default wait: 3 seconds)
- Use `--wait N` to increase wait time between searches if needed
- Headless mode (`--headless`) is faster but you can't log in manually (only works if you've already saved a session)

### Photo Geocoder
- Requires `exiftool` to be installed on your system
- Uses Nominatim API for reverse geocoding (respects rate limits)
- Caches geocoding results to avoid repeated API calls

## 🛠️ Development

Install with dev dependencies:
```bash
uv pip install -e ".[dev]"
```

## 📄 License

MIT
