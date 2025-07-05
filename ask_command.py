import asyncio
import traceback
import google.generativeai as genai
from pyrogram import Client, filters
from pyrogram.types import Message
from wordle_solver import WordleSolver # NEW: Import the solver

# Define the persona prompt here, so it can be reused across functions
PERSONA_PROMPT = """You are responding as if you are the actual user whose account this is. You should:

- Write in a natural, human way without any AI-like formalities
- Use casual, conversational language like a real person would
- Be helpful but sound like you're just knowledgeable, not like an AI
- Don't mention being an AI, assistant, or any technical terms about yourself
- Respond as if you personally know the information and are sharing it
- Use the same tone and style a human would use in Telegram chats
- Be concise unless specifically asked for detailed explanations
- Sound natural and authentic in all responses

Remember: You ARE this person, not an AI helping them. Respond accordingly."""

# Initialize the Wordle Solver globally or within the function if preferred
wordle_solver = WordleSolver()


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
    
    # Store the original message ID for editing the "thinking" status
    original_message_id = message.id 
    # Use chat_id for sending new messages
    chat_id = message.chat.id
    
    try:
        await client.edit_message_text(chat_id=chat_id, message_id=original_message_id, text="💭") # Emoji for thinking

        # --- Grammar Correction (Modified) ---
        if sub_cmd == "g":
            if message.reply_to_message and message.reply_to_message.text:
                text_to_correct = message.reply_to_message.text
            elif len(command_parts) > 2:
                text_to_correct = command_parts[2]
            else:
                await client.send_message( # Changed to send_message
                    chat_id=chat_id,
                    text="🤔 Please provide text to correct or reply to a message.\nUsage: `.ask g <text>` or reply to a message with `.ask g`"
                )
                return

            # Persona applied to grammar prompt
            prompt = f"{PERSONA_PROMPT}\n\nCorrect the grammar and spelling of the following text. Provide only the corrected text, without any introductory or concluding remarks.\n\nText to correct:\n\"{text_to_correct}\""
            
            response = await asyncio.to_thread(userbot_instance.gemini_model.generate_content, prompt)
            corrected_text = response.text if response.candidates else "❌ Could not correct grammar."
            
            # Clean up AI-specific phrases (already present, ensuring robustness)
            corrected_text = corrected_text.replace("AI output:", "").replace("Envo response:", "").strip()
            corrected_text = corrected_text.replace("Corrected text:", "").strip() # Added specific cleaning for this prompt

            await client.send_message( # Changed to send_message
                chat_id=chat_id,
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
                await client.send_message( # Changed to send_message
                    chat_id=chat_id,
                    text="🤔 Please provide text to translate or reply to a message.\nUsage: `.ask t <lang> <text>` or reply to a message with `.ask t <lang>`"
                )
                return

            # Persona applied to translation prompt
            prompt = f"{PERSONA_PROMPT}\n\nTranslate the following text into {target_lang}. Provide only the translated text, without any introductory or concluding remarks.\n\nText to translate:\n\"{text_to_translate}\""
            
            response = await asyncio.to_thread(userbot_instance.gemini_model.generate_content, prompt)
            translated_text = response.text if response.candidates else "❌ Could not translate."
            
            # Clean up AI-specific phrases (already present, ensuring robustness)
            translated_text = translated_text.replace("AI output:", "").replace("Envo response:", "").strip()
            translated_text = translated_text.replace("Translated text:", "").strip() # Added specific cleaning for this prompt

            await client.send_message( # Changed to send_message
                chat_id=chat_id,
                text=f"🌍 **Translated ({target_lang}):** {translated_text}" # Emoji for translation
            )

        # --- General Question ---
        elif len(command_parts) > 1:
            user_question = message.text[len(command_parts[0]) + 1:].strip() # Get everything after .ask
            
            # Check if it's a general question or just a sub_cmd without content
            if not user_question:
                await client.send_message( # Changed to send_message
                    chat_id=chat_id,
                    text="🤔 Please provide a question. Usage: `.ask <your question>`"
                )
                return

            # Persona applied to general question
            full_prompt = f"{PERSONA_PROMPT}\n\nHere's the question I want you to answer:\n{user_question}"
            
            response = await asyncio.to_thread(userbot_instance.gemini_model.generate_content, full_prompt) 
            ai_response = response.text if response.candidates else "❌ No response from model."
            
            # Clean up AI-specific phrases (already present, ensuring robustness)
            ai_response = ai_response.replace("AI output:", "").replace("Envo response:", "").strip()

            await client.send_message( # Changed to send_message
                chat_id=chat_id,
                text=f"✨ {ai_response}" # Emoji for general response
            )
        else:
            await client.send_message( # Changed to send_message
                chat_id=chat_id,
                text="Command usage:\n"
                     "✨ General: `.ask <your question>`\n"
                     "✍️ Grammar: `.ask g <text/reply>`\n"
                     "🌍 Translate: `.ask t <lang> <text/reply>`"
            )

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in ask_ai_command: {e}\n{error_trace}")
        await client.send_message( # Changed to send_message
            chat_id=chat_id,
            text=f"❌ An error occurred with the command: {e}"
        )
        await userbot_instance.log_error(f"Error in ask_ai_command: {str(e)}\n\nTraceback:\n{error_trace}", message)


# Function for analyzing the word guessing game
async def analyse_word_command(userbot_instance, client: Client, message: Message):
    """
    Analyzes WordSeekBot game state to guess the secret word using a dedicated solver.
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
        await client.send_message( # Changed to send_message
            chat_id=message.chat.id,
            text="🤔 Please provide the game state. Usage: `.analyse <game state lines>` or reply to a message with `.analyse`\n\nExample:\n`.analyse 🟥🟥🟥🟥🟥 THREE\n🟨🟥🟥🟨🟥 AROMA`"
        )
        return

    original_message_id = message.id # Keep original message ID for editing
    chat_id = message.chat.id # Get chat ID for sending new messages

    await client.edit_message_text(chat_id=chat_id, message_id=original_message_id, text="🧠 Analyzing game state... Please wait.") # Emoji for thinking/analysis

    try:
        # Use the dedicated WordleSolver for the logic
        possible_words = wordle_solver.solve(game_state_lines)
        
        if possible_words:
            # If multiple possibilities, ask AI to pick the "most likely" one with the persona
            # This leverages the AI's natural language understanding and general knowledge
            # to pick the best word, but only from the logically valid list.
            if len(possible_words) > 1:
                ai_selection_prompt = (
                    f"{PERSONA_PROMPT}\n\n" # Apply persona here
                    "I'm playing a 5-letter word guessing game. Based on my previous guesses, the possible secret words are now narrowed down to these options: "
                    f"{', '.join(possible_words)}. "
                    "Which single word do you think is the MOST LIKELY answer from this list, considering typical word frequencies in such games? "
                    "Just tell me that one 5-letter word, nothing else."
                )
                response = await asyncio.wait_for(
                    asyncio.to_thread(userbot_instance.gemini_model.generate_content, ai_selection_prompt),
                    timeout=15 # Shorter timeout for AI selection
                )
                selected_word = response.text.strip() if response.candidates else ""
                selected_word = ''.join(filter(str.isalpha, selected_word)).upper()
                
                if selected_word in possible_words: # Ensure AI picked from our list
                    final_word = selected_word
                else: # Fallback if AI gets it wrong or returns garbage
                    final_word = possible_words[0] # Just pick the first one as a default fallback
            else: # Only one possibility, it's the final word
                final_word = possible_words[0]

        else: # No possible words returned by solver
            final_word = None

        if final_word and len(final_word) == 5:
            await client.send_message( # Changed to send_message
                chat_id=chat_id,
                text=f"**{final_word}**" # Just the word, bolded
            )
        else:
             await client.send_message( # Changed to send_message
                chat_id=chat_id,
                text=f"❌ Analysis complete, but I couldn't clearly determine a 5-letter word. My solver found {len(possible_words)} potential matches. It's possible the input had an error or there isn't enough information yet."
                     "\n\nMake sure the input format is correct (emojis followed by word, one guess per line)."
            )

    except asyncio.TimeoutError:
        await client.send_message( # Changed to send_message
            chat_id=chat_id,
            text="⏳ Analysis timed out. The AI took too long to select the best word. Please try again or provide more precise hints."
        )
        await userbot_instance.log_error(f"Analysis timed out for message: {message.text}", message)
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in analyse_word_command: {e}\n{error_trace}")
        await client.send_message( # Changed to send_message
            chat_id=chat_id,
            text=f"❌ An error occurred during analysis: {e}"
        )
        await userbot_instance.log_error(f"Error in analyse_word_command: {str(e)}\n\nTraceback:\n{error_trace}", message)
