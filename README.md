# 🌟 Bryceriel Archive

Fan archive for the r/Bryceriel community — a curated database of theories, parallels, receipts, and fanart for the Bryce + Azriel ship across Sarah J. Maas's Maasverse.

---

## 📁 File structure

```
bryceriel/
├── index.html       ← The full site (single-page app)
├── coletar.py       ← Collection script (runs on YOUR PC, NOT online)
├── README.md        ← This file
└── data/
    └── posts.json   ← Reddit posts + AI analysis (auto-generated)
```

---

## 🚀 Quick start

### To run the site locally:
1. Open `index.html` in any browser (Chrome, Firefox, Edge, Safari)
2. That's it! No install needed.

### To deploy online (free):
1. Push this folder to GitHub
2. Connect Netlify to your GitHub repo
3. Netlify auto-deploys at `https://bryceriel.netlify.app`

---

## 🛠 Admin Panel

Click the **⚙ button** in the bottom-right corner.

**Password:** `Softmod1995`

The admin panel has 5 tabs:
- **Needs Review** — posts AI flagged for manual approval
- **Portfolio Queue** — fanart candidates awaiting curation
- **Canon Updates** — AI-generated retroactive updates after new book releases
- **All Posts** — full database
- **Stats** — overview

---

## 📚 Reading levels

The site has 3 reading levels:
- **Level I — Brycurious** — intro/foundational content
- **Level II — Bryceriel Student** — parallels & receipts
- **Level III — Bryceriel Scholar** — deep theories

Users choose their level on first visit (welcome screen).

---

## 🤖 The collection script (coletar.py)

This script runs on YOUR computer (NOT on Netlify) and:
1. Fetches new posts from r/Bryceriel via Arctic Shift API
2. Uses Claude AI to categorize, rate, and analyze each post
3. Updates `data/posts.json`
4. You then commit + push to update the site

### To set up:
```
pip install requests anthropic
```

### To run:
- Set your Anthropic API key in coletar.py first (line 27)
- Run: `python coletar.py`

### To update the site after running:
1. Open GitHub Desktop
2. It shows the changes to `data/posts.json`
3. Write a commit message ("Update posts")
4. Click "Commit to main" → "Push origin"
5. Netlify auto-deploys in ~30 seconds

---

## 📅 Canon Updates System

When new books release (ACOTAR 6 in Oct 2026, ACOTAR 7 in Jan 2027), the AI automatically:
1. Detects new posts discussing the new book
2. Cross-references them with old theories
3. Generates "Confirmed / Disproved / Still Open" updates
4. Posts get colored badges showing their canon status

Users vote on updates. If too many dislikes, the update gets flagged for manual review in the admin panel.

---

## 📱 Mobile-friendly

Responsive on desktop, tablet, mobile, and small phones.

---

## 🔄 Updating the site

To change anything:
1. Edit the file in your PC
2. Open GitHub Desktop
3. Commit changes
4. Push origin
5. Netlify auto-deploys

To clear someone's reading level (for testing):
- Add `?reset` to the URL: `https://bryceriel.netlify.app?reset`

---

## ⚠️ Disclaimer

This is an independent fan project. All original content (Maasverse, characters, etc.) belongs to Sarah J. Maas and Bloomsbury Publishing. Not affiliated with the author or publisher.
