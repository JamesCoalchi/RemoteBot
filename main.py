import subprocess
import os
import threading
import time
import tempfile
import cv2
import pyautogui
import numpy as np
from dotenv import load_dotenv
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    filters
)

# Import config from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTHORIZED_USERS = os.getenv("AUTHORIZED_USERS").split(";")
try:
    RECORD_FPS = float(os.getenv("RECORD_FPS"))
except (ValueError, TypeError):
    RECORD_FPS = 30.0  # Default value if the .env variable is invalid or missing

try:
    MAX_RECORD_SECONDS = int(os.getenv("MAX_RECORD_SECONDS"))
except (ValueError, TypeError):
    MAX_RECORD_SECONDS = 60  # Default value if the .env variable is invalid or missing

# Setup variables
current_process = None
is_recording = False
temp_dir = None
video_writer = None
cwdir = os.getcwd()

# User authorization
def authorize(func):
    async def wrapper(update: Update, context: CallbackContext):
        if not update.message.from_user.username in AUTHORIZED_USERS:
            await update.message.reply_text("⛔ Forbidden!")
            return
        return await func(update, context)
    return wrapper

# /start command
@authorize
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🤖 Check \n\n"
        "Available commands:\n"
        "/cmd [command] - Run command.\n"
        "/screenshot - Take a screenshot.\n"
        "/record_start - Start screen recording.\n"
        "/record_stop - Stop and send screen recording\n"
        "/help - Show help"
    )

# /cmd command
@authorize
async def execute_command(update: Update, context: CallbackContext):
    start_time = time.time()
    
    global cwdir, current_process

    command = update.message.text.replace('/cmd', '', 1).strip()
    
    if not command:
        await update.message.reply_text("ℹ️ Requires a command after: /cmd")
        return

    try:
        if command.startswith('cd '):
            new_dir = command[3:].strip()
            if new_dir == "":
                new_dir = os.path.expanduser("~")
            new_dir = os.path.abspath(os.path.join(cwdir, new_dir))
            if os.path.isdir(new_dir):
                cwdir = new_dir
                await update.message.reply_text(f"📂 Dir changed to: {cwdir}")
            else:
                await update.message.reply_text(f"⚠️ Dir not found: {new_dir}")
            return
        
        if current_process:
            current_process.kill()
            current_process = None

        current_process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            cwd=cwdir
        )

        try:
            # Communicate with the process, timeout after 15 seconds
            stdout, stderr = current_process.communicate(timeout=15)

            elapsed_time = time.time() - start_time

            output = ""
            if stdout:
                output += f"Output:\n{stdout}\nCompleted in {elapsed_time} seconds."
            if stderr:
                output += f"⚠️ Error:\n{stderr}\nCompleted in {elapsed_time} seconds."
            
            if not output:
                output = f"Completed in {elapsed_time} seconds. No output."
            
            if len(output) > 4096:
                output = output[:4000] + "\n... (max length)\nCompleted in {elapsed_time} seconds."

            await update.message.reply_text(output)

        except subprocess.TimeoutExpired:
            # Timeout, kill the process and notify the user
            current_process.kill()
            stdout, stderr = current_process.communicate()
            elapsed_time = time.time() - start_time
            await update.message.reply_text(f"⌛ Timed out after {elapsed_time} seconds! Process killed.")
        
        # Reset the current process tracking
        current_process = None

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

# /screenshot command
@authorize
async def send_screenshot(update: Update, context: CallbackContext):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        
        with open(filename, 'rb') as photo:
            await update.message.reply_photo(photo=InputFile(photo))
        
        os.remove(filename)
    except Exception as e:
        await update.message.reply_text(f"⚠️: {str(e)}")

# /record_start command
@authorize
async def record_start(update: Update, context: CallbackContext):
    global is_recording, temp_dir, video_writer
    
    if is_recording:
        await update.message.reply_text("⚠️: Recording alerady running!")
        return

    is_recording = True
    temp_dir = tempfile.mkdtemp()
    
    screen_size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(temp_dir, f"recording_{timestamp}.avi")
    
    video_writer = cv2.VideoWriter(output_file, fourcc, RECORD_FPS, screen_size)
    
    threading.Thread(target=record_screen, args=(update, context)).start()

    await update.message.reply_text(f"🎥 Started recording with {RECORD_FPS} frames per second.")

def record_screen(update: Update, context: CallbackContext):
    global is_recording, video_writer
    start_time = time.time()
    
    while is_recording and (time.time() - start_time) < MAX_RECORD_SECONDS:
        try:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            video_writer.write(frame)
            time.sleep(1/RECORD_FPS)
        except Exception as e:
            threading.Thread(target=send_error_message, args=(update, context, e)).start()
            break

    video_writer.release()

def send_error_message(update: Update, context: CallbackContext, error: Exception):
    try:
        error_message = f"⚠️ Recording error: {str(error)}"
        context.application.bot.send_message(chat_id=update.message.chat_id, text=error_message)
    except Exception as ex:
        print(f"Error sending message: {str(ex)}")

# /record_stop command
@authorize
async def record_stop(update: Update, context: CallbackContext):
    global is_recording, temp_dir
    
    if not is_recording:
        await update.message.reply_text("⚠️ No active recording!")
        return
    
    is_recording = False
    time.sleep(1)
    
    try:
        video_path = [f for f in os.listdir(temp_dir) if f.endswith('.avi')][0]
        full_path = os.path.join(temp_dir, video_path)
        
        with open(full_path, 'rb') as video_file:
            await update.message.reply_video(
                video=InputFile(video_file),
                supports_streaming=True
            )
        await update.message.reply_text("✅ Video sent!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error sending video!: {str(e)}. Retrying...")
        try:
            video_path = [f for f in os.listdir(temp_dir) if f.endswith('.avi')][0]
            full_path = os.path.join(temp_dir, video_path)
            
            with open(full_path, 'rb') as video_file:
                await update.message.reply_video(
                    video=InputFile(video_file),
                    supports_streaming=True
                )
            await update.message.reply_text("✅ Video sent!")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error sending video!: {str(e)}.")
    finally:
        if os.path.exists(temp_dir):
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    os.unlink(os.path.join(root, f))
            os.rmdir(temp_dir)

# /help command
@authorize
async def help_command(update: Update, context: CallbackContext):
    await start(update, context)

# Entry point
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cmd", execute_command))
    application.add_handler(CommandHandler("screenshot", send_screenshot))
    application.add_handler(CommandHandler("record_start", record_start))
    application.add_handler(CommandHandler("record_stop", record_stop))

    application.run_polling()

if __name__ == '__main__':
    main()