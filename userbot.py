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
           If the message is a reply, it quotes the replied-to message's text.
           Otherwise, it quotes the user's own message text.
           The generated quote will always reply to the message whose content was quoted.
        """
        
        # 1. Determine the text to be quoted and the message to which the quote should reply.
        text_to_quote = message.text # Default: quote the user's own message
        target_reply_id = message.id # Default: quote replies to the user's own message

        # Skip if message is a command or from another bot (userbot only processes own messages)
        if message.text and message.text.startswith('.') or (message.from_user and message.from_user.is_bot):
            return

        # Check if the message is a reply to another message
        if message.reply_to_message:
            # If it's a reply, we want to quote the text of the message it's replying to.
            # Ensure the replied-to message actually contains text.
            if message.reply_to_message.text:
                text_to_quote = message.reply_to_message.text
                target_reply_id = message.reply_to_message.id # Quote will reply to the original message
            else:
                # If the replied-to message has no text (e.g., photo without caption, sticker),
                # we cannot quote it meaningfully. Log and skip.
                await self.log_error(f"Cannot quote replied-to message (ID: {message.reply_to_message.id}): it has no text content.", message)
                return
        
        # IMPORTANT: Do NOT delete the user's original message (e.g., "Addis Ababa" in your example).
        # We want it to remain visible, and the quote to appear as a reply to the relevant message.
        # await message.delete() # Ensure this line is commented out or removed

        try:
            # 2. Manage QuotLyBot color setting to ensure consistency.
            if self.current_color != self.quotly_bot_color:
                if self.current_color != "default":
                    await client.send_message("@QuotLyBot", f"/qcolor {self.current_color}")
                    self.quotly_bot_color = self.current_color
                    await asyncio.sleep(0.5)  # Brief pause to allow bot to process
                else:
                    # Reset to default if user specified 'default'
                    await client.send_message("@QuotLyBot", "/qcolor default")
                    self.quotly_bot_color = "default"
                    await asyncio.sleep(0.5)

            # 3. Send the determined text to QuotLyBot for quote generation.
            quote_request = await client.send_message("@QuotLyBot", text_to_quote)

            # 4. Wait for QuotLyBot's response (the generated quote).
            response = await self.wait_for_quotly_response(client)

            if response:
                # 5. Send QuotLyBot's response as a reply to the appropriate message.
                if response.photo:
                    await client.send_photo(
                        chat_id=message.chat.id,
                        photo=response.photo.file_id,
                        caption=response.caption if response.caption else None,
                        reply_to_message_id=target_reply_id # Reply to the message whose content was quoted
                    )
                elif response.text:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=response.text,
                        reply_to_message_id=target_reply_id # Reply to the message whose content was quoted
                    )
                elif response.sticker:
                    # If QuotLyBot sends a sticker, forward it as a reply.
                    await client.send_sticker(
                        chat_id=message.chat.id,
                        sticker=response.sticker.file_id,
                        reply_to_message_id=target_reply_id # Reply to the message whose content was quoted
                    )
                else:
                    # Generic fallback for other media types from QuotLyBot.
                    await client.copy_message(
                        chat_id=message.chat.id,
                        from_chat_id="@QuotLyBot",
                        message_id=response.id,
                        reply_to_message_id=target_reply_id # Reply to the message whose content was quoted
                    )

                # 6. Clean up the messages sent to/from @QuotLyBot in its private chat.
                try:
                    await quote_request.delete()
                    await response.delete()
                except Exception as e:
                    print(f"Warning: Could not clean up QuotLyBot chat messages: {e}")

            else:
                # If QuotLyBot doesn't respond, raise an error.
                raise Exception("QuotLyBot did not respond. Please ensure you have started @QuotLyBot in its private chat.")

        except Exception as e:
            # 7. Handle any errors during the auto-quoting process.
            # Log the error to Saved Messages.
            await self.log_error(f"Auto-quote failed: {str(e)}", message)
            
            # Inform the user in the chat about the failure, replying to their message.
            await client.send_message(
                chat_id=message.chat.id,
                text=f"❌ Auto-quote failed for this interaction. Error: `{str(e)}`",
                reply_to_message_id=message.id # This error message replies to *your* message
            )
    
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
