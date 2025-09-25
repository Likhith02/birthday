# 🎉 Birthday Click‑To‑Wish App

A fun **interactive birthday link** built with Streamlit.  Every click:

- ✅ Increments a live counter stored in a SQLite database.
- 🎊 Launches confetti and shows a witty birthday wish (uses OpenAI if you provide an API key, otherwise falls back to funny default messages).
- 🔗 Redirects the visitor to the birthday person's LinkedIn profile.
- 📝 Allows visitors to leave an optional public roast/wish.

This project is a playful side‑project demonstrating how to combine data, generative AI and a tiny web app.

## ⚡ Quick start (local)

1. **Clone this repo and create a virtual environment**
   ```bash
   git clone https://github.com/Likhith02/birthday.git
   cd birthday
   python -m venv venv
   venv\Scripts\activate    # Windows
   # or
   source venv/bin/activate  # Linux / macOS
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set your friend’s info** and run the app:
   ```bash
   # always set these before running Streamlit
   set FRIEND_LINKEDIN_URL=https://www.linkedin.com/in/vamsi-boyapati-a98107213?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3BpmkgaQhMRcK%2B%2FzgXSUY%2BOQ%3D%3D
   set FRIEND_NAME=Vamsi Boyapati
   # optional for AI wishes
   set OPENAI_API_KEY=sk-... 

   streamlit run app.py
   ```
4. Open the local URL printed in the terminal (usually `http://localhost:8501`). Each visit counts once per browser session and triggers a confetti burst. After a short countdown, the page redirects to `FRIEND_LINKEDIN_URL`.

### Cleaning up the database

The app uses a local SQLite database (`data.db`) to store click counts and messages. To reset counts, delete `data.db`, `data.db-shm` and `data.db-wal` while the app is stopped:
```bash
del data.db data.db-shm data.db-wal
```

## 🔥 Deploy to Streamlit Cloud

1. Fork or clone this repository.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) and create a new app from your repository.
3. In the app settings, add the following secrets:
   ```
   FRIEND_LINKEDIN_URL = "https://www.linkedin.com/in/vamsi-boyapati-a98107213?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3BpmkgaQhMRcK%2B%2FzgXSUY%2BOQ%3D%3D"
   FRIEND_NAME = "Vamsi Boyapati"
   # optional
   # OPENAI_API_KEY = "sk-..."
   ```
4. Deploy and share the public URL on LinkedIn or with friends. Each click will increment the counter and direct visitors to your friend’s profile.

## ✈ Features

- **Session-safe counting**: each browser session increments the counter exactly once.
- **Confetti celebration**: triggers a multi-shot confetti effect on first visit.
- **AI or fallback wishes**: generates a witty 1-line birthday greeting using OpenAI if an API key is provided, otherwise cycles through fun messages.
- **Public roast/wish feed**: visitors can leave a short message which is stored in the database.
- **Countdown redirect**: displays a countdown and automatically redirects in a new tab, with manual fallback links and buttons to ensure compatibility across browsers.

## 🔍 Why

This mini app was built as a humorous way to celebrate a friend’s birthday while exploring Streamlit, SQLite, and generative AI. It showcases how to build a simple interactive web app that leverages environment variables and optional AI integration.

Contributions are welcome – feel free to file issues or open pull requests.
