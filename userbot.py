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
        self.quotly_bot_color = None  # Track what color QuotLyBot is currently set to
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
        """Automatically quote a message when auto-quote mode is enabled.
           Deletes the user's original message.
           If the message is a reply, the quote replies to the original message it was a reply to.
           If the message is standalone, the quote is sent as a new, standalone message.
           Always quotes the user's own message text.
           If quoting fails, the original message is restored.
        """
        original_text = message.text # Always quote the user's own message text
        
        try:
            # Skip if message is a command or from a bot
            if message.text and message.text.startswith('.') or (message.from_user and message.from_user.is_bot):
                return
            
            # Store original message for potential restoration on error
            msg_id = f"{message.chat.id}_{message.id}"
            self.original_messages[msg_id] = original_text
            
            # 1. Delete the original message (as requested, in all scenarios)
            await message.delete()
            
            # 2. Determine target_reply_id based on whether the original message was a reply
            target_reply_id = None
            if message.reply_to_message:
                target_reply_id = message.reply_to_message.id
            
            # 3. Manage QuotLyBot color setting to ensure consistency
            if self.current_color != self.quotly_bot_color:
                if self.current_color != "default":
                    await client.send_message("@QuotLyBot", f"/qcolor {self.current_color}")
                    self.quotly_bot_color = self.current_color
                    await asyncio.sleep(0.5)  # Brief pause
                else:
                    await client.send_message("@QuotLyBot", "/qcolor default")
                    self.quotly_bot_color = "default"
                    await asyncio.sleep(0.5)
            
            # 4. Send the original message's text to QuotLyBot for quote generation
            quote_request = await client.send_message("@QuotLyBot", original_text)
            
            # 5. Wait for response from @QuotLyBot
            response = await self.wait_for_quotly_response(client)
            
            if response:
                # 6. Send the QuotLyBot response content.
                # It will reply if target_reply_id is set, otherwise send standalone.
                send_params = {
                    "chat_id": message.chat.id,
                }
                if target_reply_id:
                    send_params["reply_to_message_id"] = target_reply_id

                if response.photo:
                    await client.send_photo(
                        photo=response.photo.file_id,
                        caption=response.caption if response.caption else None,
                        **send_params
                    )
                elif response.text:
                    await client.send_message(
                        text=response.text,
                        **send_params
                    )
                elif response.sticker:
                    await client.send_sticker(
                        sticker=response.sticker.file_id,
                        **send_params
                    )
                else:
                    await client.copy_message(
                        from_chat_id="@QuotLyBot",
                        message_id=response.id,
                        **send_params
                    )
                
                # 7. Clean up QuotLyBot chat messages
                try:
                    await quote_request.delete()
                    await response.delete()
                except Exception as e:
                    print(f"Warning: Could not clean up QuotLyBot chat messages: {e}")
                    pass # Continue even if cleanup fails
                
                # Remove from cache since processing is complete
                if msg_id in self.original_messages:
                    del self.original_messages[msg_id]
            
            else:
                # If QuotLyBot doesn't respond, raise an error
                raise Exception("QuotLyBot didn't respond. Make sure you've started @QuotLyBot first.")
        
        except Exception as e:
            # Handle error: restore original message and log
            try:
                # Restore the original message by sending it back to the same chat
                await client.send_message(message.chat.id, original_text)
                    
                await self.log_error(f"Auto-quote failed, original message restored: {str(e)}", message)
                
                # Remove from cache since we restored it
                if msg_id in self.original_messages:
                    del self.original_messages[msg_id]
                    
            except Exception as restore_error:
                # If restoration also fails, log both errors
                await self.log_error(f"Auto-quote failed and couldn't restore message. Original error: {str(e)}, Restore error: {str(restore_error)}", message)
    
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
        
        try:
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
                
        except Exception as e:
            error_msg = str(e)
            if "AUTH_KEY_DUPLICATED" in error_msg:
                print("⚠️ Session is being used elsewhere. Userbot will wait...")
                # Wait and retry periodically
                while True:
                    await asyncio.sleep(60)  # Wait 1 minute
                    try:
                        await self.client.start()
                        print("✅ Userbot reconnected successfully!")
                        self.is_connected = True
                        break
                    except:
                        continue
            else:
                print(f"❌ Userbot error: {error_msg}")
                # Keep the web server running even if userbot fails
                while True:
                    await asyncio.sleep(10)
