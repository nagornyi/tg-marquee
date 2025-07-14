# TG Marquee

Simple Flask application in Python that fetches messages from a Telegram channel using Telethon and displays them as a scrolling marquee in the browser.

# Prerequisites

1. You need a phone number to use the Telegram API, you've probably already got one.
2. You need to use your personal Telegram API credentials for authorisation (api_id and api_hash), please get them here https://my.telegram.org/apps
3. Get the Telegram channel ID from the channel you want to retrieve your messages from. This is a long negative number, you can easily find the channel ID if you open your channel in Telegram Web UI, it's the last part of the URL. If the channel URL is `https://web.telegram.org/a/#-1001234567890`, then the channel ID would be `-1001234567890`.
4. Generate the unique Telegram user string session (you'll have to enter your phone number, including the '+' sign and the country code, e.g. +99-10-0000-0000):
```sh
python generate_session.py --api_id YOUR_API_ID --api_hash YOUR_API_HASH
```

# Installation

Create `.env' file with Admin Password and Secret Key (make this key long and random for better security):
```sh
ADMIN_PASSWORD="[YOUR_SECURE_PASSWORD]"
SECRET_KEY="[YOUR_VERY_SECRET_KEY]"
TG_STRING_SESSION="[USER STRING SESSION]"
```

Install packages:
```sh
pip3 install -r requirements.txt
```

Run the app in Development mode:

```sh
python3 app.py
```

Run the app in Production mode:

```sh
gunicorn app:app
```

# Configuration

If you are running this application on the server, you will need to copy the `.env` file to the server first.

Open the admin page `http://127.0.0.1:8000/admin`, then add your Telegram API credentials and channel ID (your credentials are stored in a local database on the same instance). Your admin password is the string you exported to the `ADMIN_PASSWORD` environment variable from the `.env` file, please keep it safe. You can also change the update interval and marquee scrolling speed from the admin page.

The first time you access Telegram API with your credentials, Telegram will ask you to enter a confirmation code and the file `user_session.session` will be created. Please copy this file to the server where you want to deploy this application if you don't want to enter the confirmation code again.

# Usage

Open `http://127.0.0.1:8000` to see the scrolling marquee, it will update automatically every 60 seconds (the default period that can be changed along with the scrolling speed). The marquee will retrieve all the messages from your Telegram channel using the channel ID that you have specified on the admin page. The new messages will be placed at the beginning of the scrolling marquee.