"""
Telegram userbot implementation using Pyrogram.
Handles auto-quote functionality with @QuotLyBot integration.
"""

import asyncio
import json
import os
import re
from typing import Optional, Dict, Any
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config

class TelegramUserbot:
    def __init__(self):
        self.config = Config()
        self.client = None
        self.auto_quote_enabled = False
        self.current_color = "default"
        self.pending_color_change = None
        self.original_messages = {}  # Store original messages for error recovery
        self.load_state()
        
    def load_state(self):
        """Load userbot state from JSON file."""
        try:
            with open('state.json', 'r') as f:
                state = json.load(f)
                self.auto_quote_enabled = state.get('auto_quote_enabled', False)
                self.current_color = state.get('current_color', 'default')
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_state()
    
    def save_state(self):
        """Save userbot state to JSON file."""
        state = {
            'auto_quote_enabled': self.auto_quote_enabled,
            'current_color': self.current_color
        }
        with open('state.json', 'w') as f:
            json.dump(state, f, indent=2)
    
    async def log_error(self, error_msg: str, original_message: Optional[Message] = None):
        """Send error messages to Saved Messages."""
        try:
            me = await self.client.get_me()
            error_text = f"🚨 **Userbot Error**\n\n{error_msg}"
            
            if original_message:
                error_text += f"\n\n**Original Message:**\nChat: {original_message.chat.title or original_message.chat.first_name}\nText: {original_message.text}"
            
            await self.client.send_message("me", error_text)
        except Exception as e:
            print(f"Failed to log error: {e}")
    
    async def setup_client(self):
        """Initialize Pyrogram client with session string."""
        try:
            self.client = Client(
                "userbot",
                session_string=self.config.SESSION_STRING
            )
            return True
        except Exception as e:
            print(f"Failed to setup client: {e}")
            return False
    
    async def handle_quote_command(self, client: Client, message: Message):
        """Handle .q commands for quote functionality."""
        try:
            # Delete the command message
            await message.delete()
            
            text = message.text.strip()
            if not text.startswith('.q'):
                return
            
            # Parse command
            command_parts = text[2:].strip().split(' ', 1)
            
            if not command_parts or command_parts[0] == '':
                return
            
            command = command_parts[0].lower()
            
            # Handle start/stop commands
            if command == 'start':
                self.auto_quote_enabled = True
                self.save_state()
                await client.send_message("me", "✅ **Auto-quote mode enabled**\nAll your messages will now be automatically quoted.")
                return
            
            elif command == 'stop':
                self.auto_quote_enabled = False
                self.save_state()
                await client.send_message("me", "⏹️ **Auto-quote mode disabled**\nMessages will no longer be automatically quoted.")
                return
            
            # Handle color and text commands
            if len(command_parts) == 2:
                # .q colorname text
                color_name = command_parts[0]
                text_to_quote = command_parts[1]
                await self.quote_with_color(client, message, color_name, text_to_quote)
            
            elif len(command_parts) == 1:
                # .q colorname (set color for future quotes)
                color_name = command_parts[0]
                self.current_color = color_name
                self.save_state()
                await client.send_message("me", f"🎨 **Color set to: {color_name}**\nFuture quotes will use this color.")
        
        except Exception as e:
            await self.log_error(f"Error in handle_quote_command: {str(e)}", message)
    
    async def quote_with_color(self, client: Client, original_message: Message, color_name: str, text: str):
        """Send quote with specific color to @QuotLyBot."""
        try:
            # Store original message for potential restoration
            msg_id = f"{original_message.chat.id}_{original_message.id}"
            
            # Send color command to QuotLyBot
            color_msg = await client.send_message("@QuotLyBot", f"/qcolor {color_name}")
            
            # Wait for color confirmation (short delay)
            await asyncio.sleep(2)
            
            # Send the text to be quoted
            quote_request = await client.send_message("@QuotLyBot", text)
            
            # Wait for QuotLyBot response
            response = await self.wait_for_quotly_response(client)
            
            if response:
                # Send the QuotLyBot response content as your own message
                if response.photo:
                    # If it's a photo (quote image)
                    await client.send_photo(
                        original_message.chat.id,
                        response.photo.file_id,
                        caption=response.caption if response.caption else None
                    )
                elif response.text:
                    # If it's a text message
                    await client.send_message(original_message.chat.id, response.text)
                elif response.sticker:
                    # If it's a sticker
                    await client.send_sticker(original_message.chat.id, response.sticker.file_id)
                else:
                    # For any other media type, copy the message
                    await client.copy_message(original_message.chat.id, "@QuotLyBot", response.id)
                
                # Clean up QuotLyBot chat
                await color_msg.delete()
                await quote_request.delete()
                if response:
                    await response.delete()
            
            else:
                raise Exception("No response received from QuotLyBot")
        
        except Exception as e:
            await self.log_error(f"Error in quote_with_color: {str(e)}", original_message)
            # Restore original message if possible
            await client.send_message(original_message.chat.id, f"❌ Quote failed: {text}")
    
    async def auto_quote_message(self, client: Client, message: Message):
        """Automatically quote a message when auto-quote mode is enabled."""
        original_text = message.text
        try:
            # Skip if message is a command or from bot
            if message.text.startswith('.') or message.from_user.is_bot:
                return
            
            # Store original message for potential restoration
            msg_id = f"{message.chat.id}_{message.id}"
            self.original_messages[msg_id] = original_text
            
            # Delete original message first
            await message.delete()
            
            # No need to send /start to QuotLyBot
            
            # Send color command if not default
            if self.current_color != "default":
                await client.send_message("@QuotLyBot", f"/qcolor {self.current_color}")
                await asyncio.sleep(1)
            
            # Send text to quote
            quote_request = await client.send_message("@QuotLyBot", original_text)
            
            # Wait for response
            response = await self.wait_for_quotly_response(client)
            
            if response:
                # Send the QuotLyBot response content as your own message
                if response.photo:
                    # If it's a photo (quote image)
                    await client.send_photo(
                        message.chat.id,
                        response.photo.file_id,
                        caption=response.caption if response.caption else None
                    )
                elif response.text:
                    # If it's a text message
                    await client.send_message(message.chat.id, response.text)
                elif response.sticker:
                    # If it's a sticker
                    await client.send_sticker(message.chat.id, response.sticker.file_id)
                else:
                    # For any other media type, copy the message
                    await client.copy_message(message.chat.id, "@QuotLyBot", response.id)
                
                # Clean up QuotLyBot chat
                try:
                    await quote_request.delete()
                    await response.delete()
                except:
                    pass
                
                # Remove from cache
                if msg_id in self.original_messages:
                    del self.original_messages[msg_id]
            
            else:
                raise Exception("QuotLyBot didn't respond. Make sure you've started @QuotLyBot first.")
        
        except Exception as e:
            # Restore original message on error
            try:
                # Send the original message back to the same chat
                if message.reply_to_message:
                    await client.send_message(
                        message.chat.id, 
                        original_text,
                        reply_to_message_id=message.reply_to_message.id
                    )
                else:
                    await client.send_message(message.chat.id, original_text)
                    
                await self.log_error(f"Auto-quote failed, message restored: {str(e)}", message)
                
                # Remove from cache since we restored it
                if msg_id in self.original_messages:
                    del self.original_messages[msg_id]
                    
            except Exception as restore_error:
                await self.log_error(f"Auto-quote failed and couldn't restore message. Original: {str(e)}, Restore error: {str(restore_error)}", message)
    
    async def wait_for_quotly_response(self, client: Client, timeout: int = 15) -> Optional[Message]:
        """Wait for QuotLyBot to respond with any message."""
        try:
            # Wait for a few seconds before checking for response
            await asyncio.sleep(3)
            
            # Get recent messages from QuotLyBot
            messages = []
            async for message in client.get_chat_history("@QuotLyBot", limit=5):
                messages.append(message)
            
            # Look for the most recent message from QuotLyBot
            for message in messages:
                if (message.from_user and 
                    hasattr(message.from_user, 'username') and
                    message.from_user.username == "QuotLyBot"):
                    return message
            
            return None
        
        except Exception as e:
            await self.log_error(f"Error waiting for QuotLyBot response: {str(e)}")
            return None
    
    async def start(self):
        """Start the userbot."""
        if not await self.setup_client():
            print("Failed to setup client")
            return
        
        # Register handlers
        @self.client.on_message(filters.me & filters.regex(r'^\.q\s'))
        async def quote_command_handler(client, message):
            await self.handle_quote_command(client, message)
        
        @self.client.on_message(filters.me & filters.text & ~filters.regex(r'^\.'))
        async def auto_quote_handler(client, message):
            if self.auto_quote_enabled:
                await self.auto_quote_message(client, message)
        
        # Start client
        await self.client.start()
        print("✅ Userbot started successfully!")
        
        # Send startup message to Saved Messages
        try:
            await self.client.send_message("me", "🤖 **Userbot Started**\n\nCommands:\n• `.q start` - Enable auto-quote\n• `.q stop` - Disable auto-quote\n• `.q color text` - Quote with color\n• `.q color` - Set default color")
        except:
            pass
        
        # Keep running
        self.is_connected = True
        print("🤖 Userbot is now monitoring messages...")
        
        # Keep the client running
        while True:
            await asyncio.sleep(1)
