# TG Marquee

Simple Flask app in Python that fetches messages from a Telegram channel using Telethon and displays them as a scrolling marquee in the browser.

# Installation

Create `.env` file with your own admin password and secret key:
```sh
ADMIN_PASSWORD="[YOUR_SECURE_PASSWORD]"
SECRET_KEY="[YOUR_VERY_SECRET_KEY]"
```

Install packages:
```sh
pip3 install -r requirements.txt
```

Run the app:
```sh
python3 site.py
```

# Configuration

If you are running this app on the server, you would need to copy `.env` file to that server first.

Open the Admin page `http://127.0.0.1:8000/admin` and add your Telegram API credentials and Channel ID (your credentials will be stored in a local database). Your admin password is the string that you exported to ADMIN_PASSWORD environment variable from `.env` file, please keep it secure.

The first time you access Telegram API with your credentials Telegram will ask you to enter a confirmation code and the `user_session.session` file will be created. Please copy this file to the server where you plan to deploy this app if you don't want to enter the confirmation code again.

# Usage

Just open `http://127.0.0.1:8000` to see the scrolling marquee, it will update automatically every 60 seconds, fetching all messages from your Telegram channel using API credentials that you configured on Admin page.
