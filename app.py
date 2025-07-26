from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from dotenv import load_dotenv
import asyncio
import redis
import os

# Default values for scroll speed and update interval
DEFAULT_SCROLL_SPEED = 200
DEFAULT_UPDATE_INTERVAL = 60

app = Flask(__name__)

load_dotenv()  # Load environment variables from .env file
# Retrieve admin password from environment variable
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
# Secure secret key
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
app.secret_key = SECRET_KEY
# Retrieve Telegram String Session from environment variable
TG_STRING_SESSION = os.getenv("TG_STRING_SESSION")

# Redis connection setup
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Database access functions (Redis)
def init_db():
    # No-op for Redis, but can be used for future migrations
    pass

def get_api_credentials():
    creds = redis_client.hgetall('tgmarquee:config:api')
    if not creds:
        return None
    channel_id = creds.get('channel_id')
    # Convert to int if possible
    if channel_id and channel_id.lstrip('-').isdigit():
        channel_id = int(channel_id)
    return (
        creds.get('api_id'),
        creds.get('api_hash'),
        creds.get('phone_number'),
        channel_id
    )

def get_marquee_settings():
    settings = redis_client.hgetall('tgmarquee:config:marquee')
    if not settings:
        return None
    return (
        int(settings.get('scroll_speed', DEFAULT_SCROLL_SPEED)),
        int(settings.get('update_interval', DEFAULT_UPDATE_INTERVAL))
    )

def get_config():
    api = redis_client.hgetall('tgmarquee:config:api')
    marquee = redis_client.hgetall('tgmarquee:config:marquee')
    if not api and not marquee:
        return None
    channel_id = api.get('channel_id', '')
    if channel_id and channel_id.lstrip('-').isdigit():
        channel_id = int(channel_id)
    return (
        api.get('api_id', ''),
        api.get('api_hash', ''),
        api.get('phone_number', ''),
        channel_id,
        int(marquee.get('scroll_speed', DEFAULT_SCROLL_SPEED)),
        int(marquee.get('update_interval', DEFAULT_UPDATE_INTERVAL))
    )

def set_config(api_id, api_hash, phone_number, channel_id, scroll_speed=DEFAULT_SCROLL_SPEED, update_interval=DEFAULT_UPDATE_INTERVAL):
    redis_client.hset('tgmarquee:config:api', mapping={
        'api_id': api_id,
        'api_hash': api_hash,
        'phone_number': phone_number,
        'channel_id': channel_id
    })
    redis_client.hset('tgmarquee:config:marquee', mapping={
        'scroll_speed': scroll_speed,
        'update_interval': update_interval
    })


# Telegram API access functions

async def fetch_messages():
    """Fetch all messages from Telegram channel"""
    api_creds = get_api_credentials()
    if not api_creds:
        return []

    api_id, api_hash, phone_number, channel_id = api_creds
    # Initialize Telegram Client
    client = TelegramClient(StringSession(TG_STRING_SESSION), api_id, api_hash)
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
    
    except errors.FloodWaitError as e:
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
        client = TelegramClient(StringSession(TG_STRING_SESSION), api_id, api_hash)
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
    # If config is None, prepopulate with defaults for scroll_speed and update_interval
    if config is None:
        config = ['', '', '', '', DEFAULT_SCROLL_SPEED, DEFAULT_UPDATE_INTERVAL]
    # If scroll_speed or update_interval are None, set to defaults
    config = list(config)
    if config[4] is None:
        config[4] = DEFAULT_SCROLL_SPEED
    if config[5] is None:
        config[5] = DEFAULT_UPDATE_INTERVAL
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
    
    # Handle case where no configuration exists
    if settings is None:
        settings_dict = {
            'scroll_speed': DEFAULT_SCROLL_SPEED,
            'update_interval': DEFAULT_UPDATE_INTERVAL
        }
    else:
        settings_dict = {
            'scroll_speed': settings[0] if settings[0] is not None else DEFAULT_SCROLL_SPEED,
            'update_interval': settings[1] if settings[1] is not None else DEFAULT_UPDATE_INTERVAL
        }    
    return jsonify(settings_dict)

# Initialize database when module is imported
init_db()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
