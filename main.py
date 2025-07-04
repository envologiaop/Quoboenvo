"""
Main entry point for the Telegram userbot with Flask wrapper for Render deployment.
This file starts both the Flask web server and the Pyrogram userbot.
"""

import asyncio
import threading
import os
from flask import Flask, jsonify
from userbot import TelegramUserbot

# Initialize Flask app for Render web service requirement
app = Flask(__name__)

# Global userbot instance
userbot_instance = None

@app.route('/')
def health_check():
    """Health check endpoint for Render deployment."""
    return jsonify({
        "status": "running",
        "service": "telegram_userbot",
        "auto_quote_enabled": userbot_instance.auto_quote_enabled if userbot_instance else False
    })

@app.route('/status')
def status():
    """Status endpoint showing userbot information."""
    if userbot_instance:
        return jsonify({
            "userbot_running": userbot_instance.is_connected if hasattr(userbot_instance, 'is_connected') else False,
            "auto_quote_mode": userbot_instance.auto_quote_enabled,
            "current_color": userbot_instance.current_color
        })
    return jsonify({"userbot_running": False})

def run_flask():
    """Run Flask server in a separate thread."""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

async def run_userbot():
    """Run the Telegram userbot."""
    global userbot_instance
    userbot_instance = TelegramUserbot()
    await userbot_instance.start()

def start_userbot_background():
    """Start userbot in background thread for Gunicorn."""
    def run_async():
        asyncio.run(run_userbot())
    
    userbot_thread = threading.Thread(target=run_async, daemon=True)
    userbot_thread.start()

def main():
    """Main function to start both Flask and userbot."""
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run userbot in the main thread
    asyncio.run(run_userbot())

# Initialize userbot when module is imported (for Gunicorn)
start_userbot_background()

if __name__ == "__main__":
    main()
