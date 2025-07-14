import argparse
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Telegram User String Session.")
    parser.add_argument("--api_id", required=True, help="Your Telegram API ID")
    parser.add_argument("--api_hash", required=True, help="Your Telegram API Hash")
    args = parser.parse_args()

    with TelegramClient(StringSession(), args.api_id, args.api_hash) as client:
        print(client.session.save())
