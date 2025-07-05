import asyncio
import traceback
import google.generativeai as genai
from pyrogram import Client, filters
from pyrogram.types import Message
# Removed 'requests' and 'json' imports as they are no longer needed without the web search

async def ask_ai_command(userbot_instance, client: Client, message: Message):
    """
    Handle the .ask command for AI interactions.
    Supports general questions, grammar correction, and translation.
    """
    if not userbot_instance.gemini_model:
        await message.edit_text("❌ Model not configured. Please set `GEMINI_API_KEY` in your environment variables.")
        return

    command_parts = message.text.split(' ', 2)
    cmd = command_parts[0].lower()
    sub_cmd = command_parts[1].lower() if len(command_parts) > 1 else None
    
    original_message_id = message.id
    
    try:
        await message.edit_text("💭") # Emoji for thinking

        # --- Web Search with DuckDuckGo functionality has been removed ---
        # The entire 'if sub_cmd == "web":' block is no longer here.


        # --- Grammar Correction (Modified) ---
        if sub_cmd == "g":
            if message.reply_to_message and message.reply_to_message.text:
                text_to_correct = message.reply_to_message.text
            elif len(command_parts) > 2:
                text_to_correct = command_parts[2]
            else:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=original_message_id,
                    text="🤔 Please provide text to correct or reply to a message.\nUsage: `.ask g <text>` or reply to a message with `.ask g`"
                )
                return

            prompt = f"Correct the grammar and spelling of the following text:\n\n\"{text_to_correct}\"\n\nProvide only the corrected text."
            
            response = await asyncio.to_thread(userbot_instance.gemini_model.generate_content, prompt)
            corrected_text = response.text if response.candidates else "❌ Could not correct grammar."
            
            # Clean up AI-specific phrases
            corrected_text = corrected_text.replace("AI output:", "").replace("Envo response:", "").strip()

            # MODIFIED: Removed the original text from the response for grammar
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=original_message_id,
                text=f"✍️ **Corrected:** {corrected_text}" # Emoji for writing/correction
            )

        # --- Translation (Modified) ---
        elif sub_cmd == "t" and len(command_parts) > 2:
            target_lang = command_parts[2].split(' ', 1)[0].strip()
            text_to_translate_parts = command_parts[2].split(' ', 1)
            text_to_translate = text_to_translate_parts[1].strip() if len(text_to_translate_parts) > 1 else None

            if not text_to_translate and message.reply_to_message and message.reply_to_message.text:
                text_to_translate = message.reply_to_message.text
            
            if not text_to_translate:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=original_message_id,
                    text="🤔 Please provide text to translate or reply to a message.\nUsage: `.ask t <lang> <text>` or reply to a message with `.ask t <lang>`"
                )
                return

            prompt = f"Translate the following text into {target_lang}:\n\n\"{text_to_translate}\"\n\nProvide only the translated text."
            
            response = await asyncio.to_thread(userbot_instance.gemini_model.generate_content, prompt)
            translated_text = response.text if response.candidates else "❌ Could not translate."
            
            # Clean up AI-specific phrases
            translated_text = translated_text.replace("AI output:", "").replace("Envo response:", "").strip()

            # Original text was already removed from translation response in a previous iteration.
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=original_message_id,
                text=f"🌍 **Translated ({target_lang}):** {translated_text}" # Emoji for translation
            )

        # --- General Question ---
        elif len(command_parts) > 1: # No longer checking for sub_cmd != "web" as "web" is removed
            user_question = message.text[len(command_parts[0]) + 1:].strip() # Get everything after .ask
            
            # Check if it's a general question or just a sub_cmd without content
            if not user_question:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=original_message_id,
                    text="🤔 Please provide a question. Usage: `.ask <your question>`"
                )
                return

            # Send general question to Gemini without tools
            response = await asyncio.to_thread(userbot_instance.gemini_model.generate_content, prompt) # Changed 'user_question' to 'prompt' here
            ai_response = response.text if response.candidates else "❌ No response from model."
            
            # Clean up AI-specific phrases
            ai_response = ai_response.replace("AI output:", "").replace("Envo response:", "").strip()

            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=original_message_id,
                text=f"✨ {ai_response}" # Emoji for general response
            )
        else:
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=original_message_id,
                text="Command usage:\n"
                     "✨ General: `.ask <your question>`\n"
                     "✍️ Grammar: `.ask g <text/reply>`\n"
                     "🌍 Translate: `.ask t <lang> <text/reply>`"
            )

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in ask_ai_command: {e}\n{error_trace}")
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=original_message_id,
            text=f"❌ An error occurred with the command: {e}"
        )
        await userbot_instance.log_error(f"Error in ask_ai_command: {str(e)}\n\nTraceback:\n{error_trace}", message)
