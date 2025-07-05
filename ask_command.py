import asyncio
import traceback
import google.generativeai as genai
from pyrogram import Client, filters
from pyrogram.types import Message

# Import the new DuckDuckGo search tool
# Make sure duckduckgo_search.py is in the same directory
import duckduckgo_search as search_tool 

# Define a custom tool for the Gemini model to perform web searches
def ddg_search(query: str):
    """
    Performs a web search using DuckDuckGo Instant Answer API.
    This tool does not require an API key.
    Returns relevant snippets or instant answers.
    """
    print(f"DEBUG: Performing DuckDuckGo search for: {query}")
    results = search_tool.search(queries=[query])
    
    # Format results for the model
    formatted_results = []
    if results:
        for r in results:
            formatted_results.append(
                f"Title: {r.get('title', 'N/A')}\n"
                f"Link: {r.get('link', 'N/A')}\n"
                f"Snippet: {r.get('snippet', 'No snippet available.')}\n"
            )
        return "\n---\n".join(formatted_results)
    return "No search results found."


async def ask_ai_command(userbot_instance, client: Client, message: Message):
    """
    Handle the .ask command for AI interactions.
    Supports general questions, grammar correction, translation, and web search.
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

        # --- Web Search with DuckDuckGo ---
        if sub_cmd == "web" and len(command_parts) > 2:
            user_question = command_parts[2]
            await message.edit_text(f"🔍 Searching: {user_question}") # Emoji for searching
            
            # Configure the Gemini model to use the ddg_search tool
            model_with_tool = userbot_instance.gemini_model.with_tools(ddg_search)
            
            # Create a chat session with the model
            chat = model_with_tool.start_chat(enable_automatic_function_calling=True)
            
            # Send the user's query
            try:
                response = await asyncio.to_thread(chat.send_message, user_question)
                
                response_text = ""
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text'):
                            response_text += part.text
                
                # Clean up AI-specific phrases
                response_text = response_text.replace("AI output:", "").replace("Envo response:", "").strip()
                # You can add more replacements here if you notice other unwanted phrases

                if response_text:
                    await client.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=original_message_id,
                        text=response_text
                    )
                else:
                    await client.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=original_message_id,
                        text="❌ No direct response after search."
                    )

            except Exception as e:
                # Catch tool_code.tool_error for tool execution failures
                if "tool_code.tool_error" in str(e):
                    await client.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=original_message_id,
                        text=f"❌ Search tool error: {e}\n\nThis might happen if the model tried to use the search tool in an unexpected way."
                    )
                else:
                    raise # Re-raise other exceptions


        # --- Grammar Correction ---
        elif sub_cmd == "g":
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

            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=original_message_id,
                text=f"✍️ **Original:** {text_to_correct}\n**Corrected:** {corrected_text}" # Emoji for writing/correction
            )

        # --- Translation ---
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

            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=original_message_id,
                text=f"🌍 **Original:** {text_to_translate}\n**Translated ({target_lang}):** {translated_text}" # Emoji for translation
            )

        # --- General Question ---
        elif len(command_parts) > 1 and sub_cmd != "web": # Ensure it's not a web search with just .ask web
            user_question = message.text[len(command_parts[0]) + 1:].strip() # Get everything after .ask
            
            # Check if it's a general question or just a sub_cmd without content
            if not user_question:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=original_message_id,
                    text="🤔 Please provide a question. Usage: `.ask <your question>` or `.ask web <your search query>`"
                )
                return

            # Send general question to Gemini without tools
            response = await asyncio.to_thread(userbot_instance.gemini_model.generate_content, user_question)
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
                     "🔍 Web Search: `.ask web <your search query>`\n"
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
