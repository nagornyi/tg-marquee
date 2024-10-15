from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from telethon import TelegramClient, errors
from dotenv import load_dotenv
import asyncio
import sqlite3
import os

app = Flask(__name__)

load_dotenv()  # Load environment variables from .env file
# Retrieve admin password from environment variable
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
# Secure secret key
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
app.secret_key = SECRET_KEY

def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect('config.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY,
            api_id TEXT,
            api_hash TEXT,
            phone_number TEXT,
            channel_id INTEGER,
            scroll_speed INTEGER,
            update_interval INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def get_config():
    conn = sqlite3.connect('config.db')
    cursor = conn.cursor()
    cursor.execute("SELECT api_id, api_hash, phone_number, channel_id, scroll_speed, update_interval FROM config WHERE id=1")
    row = cursor.fetchone()
    conn.close()
    return row

def set_config(api_id, api_hash, phone_number, channel_id, scroll_speed=200, update_interval=60):
    conn = sqlite3.connect('config.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO config (id, api_id, api_hash, phone_number, channel_id, scroll_speed, update_interval)
                      VALUES (1, ?, ?, ?, ?)''',
                   (api_id, api_hash, phone_number, channel_id, scroll_speed, update_interval))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Invalid password")
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        api_id = request.form['api_id']
        api_hash = request.form['api_hash']
        phone_number = request.form['phone_number']
        channel_id = request.form['channel_id']
        scroll_speed = request.form['scroll_speed']
        update_interval = request.form['update_interval']
        set_config(api_id, api_hash, phone_number, channel_id, scroll_speed, update_interval)
        return redirect(url_for('index'))
    
    config = get_config()
    return render_template('admin.html', config=config)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

# Health check route
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/get_messages', methods=['GET'])
def get_messages():
    # Run async code in a separate event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    messages = loop.run_until_complete(fetch_messages())
    return jsonify(messages)

@app.route('/get_settings', methods=['GET'])
def get_settings():
    conn = sqlite3.connect('config.db')
    settings = conn.execute('SELECT scroll_speed, update_interval FROM config WHERE id=1').fetchall()
    conn.close()
    settings_dict = {setting['key']: setting['value'] for setting in settings}
    return jsonify(settings_dict)

async def fetch_messages():
    """Fetch all messages from Telegram channel"""
    config = get_config()
    if not config:
        return []

    api_id, api_hash, phone_number, channel_id = config
    # Initialize Telegram Client
    client = TelegramClient('user_session', api_id, api_hash)
    await client.start(phone_number)

    messages = []
    last_message_id = 0

    try:
        while True:
            # Fetch messages in batches of 100
            batch = []
            async for message in client.iter_messages(channel_id, limit=100, offset_id=last_message_id):
                batch.append(message.text)
                last_message_id = message.id
            
            if not batch:
                break  # No more messages to fetch
            
            messages.extend(batch)
    
    except errors.FloodWait as e:
        print(f'Rate limit exceeded. Sleeping for {e.seconds} seconds.')
        await asyncio.sleep(e.seconds)
    except Exception as e:
        print(f'An error occurred: {e}')
    
    await client.disconnect()
    return messages

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=8000)
