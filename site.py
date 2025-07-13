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

# Database access functions

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
            scroll_speed INTEGER DEFAULT 200,
            update_interval INTEGER DEFAULT 60
        )
    ''')

    # Check and add new columns if they don't exist
    existing_columns = [row[1] for row in cursor.execute('PRAGMA table_info(config)')]

    # Add scroll_speed column if it doesn't exist
    if 'scroll_speed' not in existing_columns:
        cursor.execute('ALTER TABLE config ADD COLUMN scroll_speed INTEGER DEFAULT 200')

    # Add update_interval column if it doesn't exist
    if 'update_interval' not in existing_columns:
        cursor.execute('ALTER TABLE config ADD COLUMN update_interval INTEGER DEFAULT 60')

    # Update any existing rows where scroll_speed or update_interval are NULL
    cursor.execute('''
        UPDATE config
        SET scroll_speed = COALESCE(scroll_speed, 200),
            update_interval = COALESCE(update_interval, 60)
    ''')

    conn.commit()
    conn.close()

def get_api_credentials():
    conn = sqlite3.connect('config.db')
    cursor = conn.cursor()
    cursor.execute("SELECT api_id, api_hash, phone_number, channel_id FROM config WHERE id=1")
    row = cursor.fetchone()
    conn.close()
    return row

def get_marquee_settings():
    conn = sqlite3.connect('config.db')
    cursor = conn.cursor()
    cursor.execute("SELECT scroll_speed, update_interval FROM config WHERE id=1")
    row = cursor.fetchone()
    conn.close()
    return row

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
                      VALUES (1, ?, ?, ?, ?, ?, ?)''',
                   (api_id, api_hash, phone_number, channel_id, scroll_speed, update_interval))
    conn.commit()
    conn.close()

# Telegram API access functions

async def fetch_messages():
    """Fetch all messages from Telegram channel"""
    api_creds = get_api_credentials()
    if not api_creds:
        return []

    api_id, api_hash, phone_number, channel_id = api_creds
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

# Routes

@app.route('/chat')
def chat():
    return render_template('chat.html')

# Route to send a message to the configured Telegram channel
@app.route('/send_message', methods=['POST'])
def send_message():
    if not request.json or 'message' not in request.json:
        return jsonify({'ok': False, 'error': 'No message provided'}), 400
    message = request.json['message']
    api_creds = get_api_credentials()
    if not api_creds:
        return jsonify({'ok': False, 'error': 'API credentials not configured'}), 500
    api_id, api_hash, phone_number, channel_id = api_creds
    async def send():
        client = TelegramClient('user_session', api_id, api_hash)
        await client.start(phone_number)
        try:
            await client.send_message(int(channel_id), message)
            await client.disconnect()
            return True, None
        except Exception as e:
            await client.disconnect()
            return False, str(e)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ok, error = loop.run_until_complete(send())
    if ok:
        return jsonify({'ok': True})
    else:
        return jsonify({'ok': False, 'error': error}), 500
    
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
    settings = get_marquee_settings()
    settings_dict = {
        'scroll_speed': settings[0],  # This will be None if no value is present
        'update_interval': settings[1]  # This will be None if no value is present
    }
    return jsonify(settings_dict)

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=8000)
