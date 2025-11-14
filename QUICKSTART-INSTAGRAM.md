# Instagram Hashtag Search - Quick Start Guide

## 🚀 The Easiest Way (Save Your Session - RECOMMENDED!)

### **First Time Setup (Login Once):**

```bash
python instagram-hashtag-search.py --hashtag rebelscapes --users alice --save-session --login-wait 60
```

When the browser opens, log into Instagram. Your session will be saved to `.instagram-session/`

### **Every Time After (No Re-Login!):**

```bash
python instagram-hashtag-search.py --hashtag rebelscapes --users alice bob charlie --save-session
```

That's it! It will:
- ✅ Launch browser **fast** (not slow debug mode!)
- ✅ Automatically use your saved login (no re-login!)
- ✅ Check 12 posts per hashtag to find the most recent
- ✅ Save results to `instagram_results.json`

**Your login stays saved** in `.instagram-session/` directory. Delete that folder if you want to log in as a different user.

---

## 📖 Alternative Methods

### **Method 2: Use a File with Many Usernames**

Create `myusers.txt`:
```
alice
bob
charlie
john_doe
```

Then run:
```bash
python instagram-hashtag-search.py --hashtag rebelscapes --users-file myusers.txt --save-session
```

---

## ⚙️ Useful Options

### **Check More Posts** (default: 12)
```bash
--max-posts 20
```
Higher = slower but more thorough. Good if hashtag has many recent posts.

### **Wait Longer Between Searches** (default: 3 seconds)
```bash
--wait 5
```
Use if Instagram is rate-limiting you.

### **Custom Output File**
```bash
--output my_results.json
```

### **All Options Combined**
```bash
python instagram-hashtag-search.py \
  --hashtag rebelscapes \
  --users-file myusers.txt \
  --save-session \
  --max-posts 15 \
  --wait 4 \
  --output results.json
```

---

## 🔧 Troubleshooting

### **Not staying logged in?**
- Make sure you're using `--save-session` flag
- Session data is stored in `.instagram-session/` directory
- If login still doesn't persist, delete `.instagram-session/` and try again

### **"No posts found" but I can see them**
- Make sure you're logged into Instagram (use `--login-wait 60` on first run)
- Try increasing `--max-posts` to check more posts
- Try increasing `--wait` between searches

### **Need to log in as different Instagram user?**
- Delete the `.instagram-session/` directory
- Run with `--save-session --login-wait 60` again
- Log in with the new account

### **Script is too slow**
- Reduce `--max-posts` to check fewer posts per hashtag
- Each post takes ~2 seconds to check
- Default 12 posts = ~24 seconds per hashtag

---

## 💡 Tips

1. **Always use `--save-session`** - saves your login permanently!
2. **First run?** Use `--max-posts 5 --login-wait 60` to test quickly
3. **Many users?** Put them in a text file (one per line)
4. **Rate limiting?** Increase `--wait` to 5-10 seconds
5. **Results file** is overwritten each run - rename it if you want to keep old results
6. **Session not persisting?** Delete `.instagram-session/` folder and log in again

---

## 📊 Output Example

```json
{
  "alice": {
    "username": "alice",
    "hashtag": "#rebelscapes_alice",
    "post_count": 24,
    "posts_checked": 12,
    "dates_found": 12,
    "most_recent_date": "2025-11-10 14:30:00",
    "status": "success"
  }
}
```

---

## 🆘 Need Help?

Run with `--help` to see all options:
```bash
python instagram-hashtag-search.py --help
```


