import asyncio
import os
import google.generativeai as genai
from pyrogram import Client
from pyrogram.types import Message

async def ask_ai_command(ubot, client: Client, message: Message):
    """
    Handles the .ask, .ask g (grammar), and .ask t (translate) commands to query Envo AI.
    It incorporates context from replied-to messages.
    """
    if message.forward_from:
        await message.edit_text("`I cannot process forwarded messages for Envo queries.`")
        await asyncio.sleep(3)
        await message.delete()
        return

    if not ubot.gemini_model:
        await message.edit_text("`Envo AI is not configured. Please set GEMINI_API_KEY.`")
        await asyncio.sleep(3)
        await message.delete()
        return

    # Get text from replied message if it exists
    source_text_from_reply = ""
    if message.reply_to_message:
        if message.reply_to_message.text:
            source_text_from_reply = message.reply_to_message.text
        elif message.reply_to_message.caption:
            source_text_from_reply = message.reply_to_message.caption
    
    # Remove the initial '.ask' to get the arguments string
    command_args_string = message.text[len('.ask'):].strip()
    
    ai_prompt = ""
    action_description = ""
    
    # Check for sub-commands like 'g' (grammar) or 't' (translate)
    if command_args_string.lower().startswith('g '): # Grammar command: .ask g [text]
        action_description = "fixing grammar and general text issues"
        text_for_ai = command_args_string[len('g '):].strip() # Get text after "g "
        
        # If no text provided directly, use replied text
        if not text_for_ai and source_text_from_reply:
            text_for_ai = source_text_from_reply
        
        if not text_for_ai:
            await message.edit_text("`Please provide text to fix grammar after .ask g or reply to a message.`")
            await asyncio.sleep(3)
            await message.delete()
            return
        
        ai_prompt = f"Correct the grammar, spelling, punctuation, and improve the overall readability of the following text. Provide only the corrected text, no additional explanations:\n\n'{text_for_ai}'"
    
    elif command_args_string.lower().startswith('t '): # Translate command: .ask t <lang> [text]
        action_description = "translating text"
        
        # Parse target language and text to translate
        # Example: "t French Hello world" -> lang="French", text="Hello world"
        parts_after_t = command_args_string[len('t '):].strip().split(maxsplit=1)
        
        target_language = parts_after_t[0].strip() if parts_after_t else ""
        text_for_ai = parts_after_t[1].strip() if len(parts_after_t) > 1 else ""

        # If no explicit text provided, use replied text
        if not text_for_ai and source_text_from_reply:
            text_for_ai = source_text_from_reply

        if not target_language:
            await message.edit_text("`Please specify a target language for translation (e.g., .ask t French I love this).`")
            await asyncio.sleep(3)
            await message.delete()
            return
        
        if not text_for_ai:
             await message.edit_text("`Please provide text to translate after .ask t <lang> or reply to a message.`")
             await asyncio.sleep(3)
             await message.delete()
             return
            
        ai_prompt = f"Translate the following text to {target_language}. Provide only the translated text, no additional explanations:\n\n'{text_for_ai}'"

    else: # General ask command: .ask <question> or .ask (with reply)
        action_description = "answering your question"
        
        user_question = command_args_string # The entire string after .ask if not 'g' or 't'
        
        if user_question and source_text_from_reply:
            # If both a question and a reply are present
            ai_prompt = f"{user_question}\n\nContext from replied message: '{source_text_from_reply}'"
        elif user_question:
            # Only a question provided after .ask
            ai_prompt = user_question
        elif source_text_from_reply:
            # Only a reply, no question after .ask
            ai_prompt = f"Please explain or summarize the following text: '{source_text_from_reply}'"
        else:
            # No question, no reply, nothing for AI to do
            await message.edit_text("`Please provide a question, a text to fix/translate, or reply to a message.`")
            await asyncio.sleep(3)
            await message.delete()
            return
        
    if not ai_prompt: # Fallback if for some reason prompt is empty (shouldn't happen with logic above)
        await message.edit_text("`Failed to formulate a valid prompt.`")
        await asyncio.sleep(3)
        await message.delete()
        return

    thinking_message = await message.edit_text(f"`Envo is {action_description}...`") # Dynamic thinking message based on action

    try:
        response = await asyncio.to_thread(ubot.gemini_model.generate_content, ai_prompt)
        
        ai_response = response.text if hasattr(response, 'text') else "No direct text response from Envo."

        if len(ai_response) > 4096: # Telegram message limit for text
            file_path = "envo_response.txt"
            with open(file_path, "w") as f:
                f.write(ai_response)
            
            await thinking_message.edit_text("`Envo response is too long. Sending as a file...`")
            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption="Envo Response"
            )
            os.remove(file_path) # Clean up the temporary file
        else:
            await thinking_message.edit_text(f"**Envo Response:**\n\n`{ai_response}`")

    except Exception as e:
        error_msg = f"Error communicating with Envo AI: {e}"
        await thinking_message.edit_text(f"`{error_msg}`")
        await ubot.log_error(error_msg, message)
