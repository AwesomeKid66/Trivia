# 🧠 Trivia Question Contributor Portal

Welcome to the official repository for the **Michael Trivia Project** — a lightweight, community-driven trivia platform. This project pulls trivia questions from structured JSON files and presents them in an interactive quiz format.

## ✍️ Contribute a Trivia Question

Want to help grow the trivia database? You can easily submit new questions using the link below — **no login or GitHub account required**.

👉 [Submit a Trivia Question](https://michaeltriviaform.fillout.com/addquestion)

- ✅ No account or sign-in needed  
- 📱 Mobile-friendly  
- 📝 Questions are reviewed before going live  

---

## 📁 Project Structure

- `questions/` — Topic-based JSON files (e.g., `star_wars.json`, `history.json`) with trivia questions and answers.
- `scripts/` — Python tools for syncing with Notion, cleaning input, and managing game logic.
- `.github/workflows/` — GitHub Actions to sync questions, validate format, and deploy updates.
- `main.py` — The interactive trivia CLI/game interface.
- `notion_sync.py` — Handles syncing new form submissions into local JSON files.

---

## 🔧 Developer Setup

Clone the repo:

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
