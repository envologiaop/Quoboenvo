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

            # Enhanced prompt for grammar correction
            prompt = f"Correct the grammar and spelling of the following text. Provide only the corrected text, without any introductory or concluding remarks.\n\nText to correct:\n\"{text_to_correct}\""
            
            response = await asyncio.to_thread(userbot_instance.gemini_model.generate_content, prompt)
            corrected_text = response.text if response.candidates else "❌ Could not correct grammar."
            
            # Clean up AI-specific phrases (already present, ensuring robustness)
            corrected_text = corrected_text.replace("AI output:", "").replace("Envo response:", "").strip()
            corrected_text = corrected_text.replace("Corrected text:", "").strip() # Added specific cleaning for this prompt

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

            # Enhanced prompt for translation
            prompt = f"Translate the following text into {target_lang}. Provide only the translated text, without any introductory or concluding remarks.\n\nText to translate:\n\"{text_to_translate}\""
            
            response = await asyncio.to_thread(userbot_instance.gemini_model.generate_content, prompt)
            translated_text = response.text if response.candidates else "❌ Could not translate."
            
            # Clean up AI-specific phrases (already present, ensuring robustness)
            translated_text = translated_text.replace("AI output:", "").replace("Envo response:", "").strip()
            translated_text = translated_text.replace("Translated text:", "").strip() # Added specific cleaning for this prompt

            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=original_message_id,
                text=f"🌍 **Translated ({target_lang}):** {translated_text}" # Emoji for translation
            )

        # --- General Question ---
        elif len(command_parts) > 1:
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
            # Prompt is now just the user's question, allowing the AI to respond naturally
            response = await asyncio.to_thread(userbot_instance.gemini_model.generate_content, user_question) 
            ai_response = response.text if response.candidates else "❌ No response from model."
            
            # Clean up AI-specific phrases (already present, ensuring robustness)
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


# NEW FUNCTION: For analyzing the word guessing game
async def analyse_word_command(userbot_instance, client: Client, message: Message):
    """
    Analyzes WordSeekBot game state to guess the secret word.
    """
    if not userbot_instance.gemini_model:
        await message.edit_text("❌ AI model not configured for analysis. Please set `GEMINI_API_KEY`.")
        return

    game_state_lines = None
    # Check if the command is a reply to a message
    if message.reply_to_message and message.reply_to_message.text:
        game_state_lines = message.reply_to_message.text
    else:
        # Otherwise, try to extract from the command itself
        text_after_command = message.text.split(' ', 1)
        if len(text_after_command) > 1 and text_after_command[1].strip():
            game_state_lines = text_after_command[1].strip()

    if not game_state_lines:
        await message.edit_text("🤔 Please provide the game state. Usage: `.analyse <game state lines>` or reply to a message with `.analyse`\n\nExample:\n`.analyse 🟥🟥🟥🟥🟥 THREE\n🟨🟥🟥🟨🟥 AROMA`")
        return

    original_message_id = message.id # Keep original message ID for editing
    await message.edit_text("🧠 Analyzing game state... Please wait.") # Emoji for thinking/analysis

    # Enhanced prompt for word analysis to get a "smarter" and cleaner response
    prompt = (
        "You are an expert at solving 5-letter word guessing games, similar to Wordle. The secret word is exactly 5 letters long.\n"
        "Here are the rules for interpreting the feedback squares:\n"
        "- 🟩 (Green square) means the letter is correct and in the correct position.\n"
        "- 🟨 (Yellow square) means the letter is correct but in the wrong position (it exists in the word, just not here).\n"
        "- 🟥 (Red square) means the letter is NOT in the word at all.\n\n"
        "Analyze the following game state, which includes previous guesses and their feedback. "
        "Based on ALL the information provided, determine the MOST LIKELY 5-letter secret word. "
        "Your response MUST be ONLY the 5-letter word itself, with no other text, punctuation, or explanation whatsoever. "
        "Do NOT include any introductory phrases like 'The word is' or 'I think the word is'. Just the word.\n\n"
        "Game state:\n"
        f"{game_state_lines}"
    )

    try:
        # Added a timeout for the AI generation
        response = await asyncio.wait_for(
            asyncio.to_thread(userbot_instance.gemini_model.generate_content, prompt),
            timeout=30 # 30-second timeout for AI response
        )
        
        predicted_word = response.text.strip() if response.candidates else ""

        # Robust post-processing to ensure ONLY the 5-letter word is extracted
        # Remove any conversational filler or formatting
        predicted_word = predicted_word.replace("AI output:", "").replace("Envo response:", "").strip()
        predicted_word = predicted_word.split('\n')[0].strip() # Take only the first line
        predicted_word = ''.join(filter(str.isalpha, predicted_word)).upper() # Filter non-alphabetic chars and convert to uppercase

        if len(predicted_word) == 5:
            # Changed the output to be more direct, as if from "you"
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=original_message_id,
                text=f"**{predicted_word}**" # Just the word, bolded
            )
        else:
             await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=original_message_id,
                text=f"❌ Analysis complete, but I couldn't clearly determine a 5-letter word. Result: `{predicted_word}`\n\n"
                     "Please ensure you provide the exact emoji/word format for the game state or that the AI has enough information."
            )

    except asyncio.TimeoutError:
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=original_message_id,
            text="⏳ Analysis timed out. The AI took too long to respond. Please try again or provide more precise hints."
        )
        await userbot_instance.log_error(f"Analysis timed out for message: {message.text}", message)
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in analyse_word_command: {e}\n{error_trace}")
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=original_message_id,
            text=f"❌ An error occurred during analysis: {e}"
        )
        await userbot_instance.log_error(f"Error in analyse_word_command: {str(e)}\n\nTraceback:\n{error_trace}", message)
