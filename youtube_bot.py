import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
import yt_dlp
import os
import tempfile
from PIL import Image

# Set up bot token
import os
API_TOKEN = os.getenv("API_TOKEN")
bot = telebot.TeleBot(API_TOKEN)

# Temporary directory for file handling
TEMP_DIR = tempfile.gettempdir()

# Custom keyboard options
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🎥 Download Video"), KeyboardButton("🖼️ Convert Image"))
    return markup

def video_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("📹 YouTube"), KeyboardButton("🎵 TikTok"))
    markup.row(KeyboardButton("🔙 Back"))
    return markup

def image_conversion_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("📷 JPG"), KeyboardButton("🖼️ PNG"))
    markup.row(KeyboardButton("📜 PDF"), KeyboardButton("🔙 Back"))
    return markup

# Function to clean temporary files
def cleanup_temp_files():
    for file in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, file)
        if os.path.isfile(file_path):
            os.unlink(file_path)

# Start command
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(
        message,
        "🎉 **Welcome to the Ultimate Media Downloader Bot!** 🎬\n\n"
        "I can help you download videos and convert images into various formats. "
        "Select an option below to get started.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# Handle "Download Video" button
@bot.message_handler(func=lambda message: message.text == "🎥 Download Video")
def select_video_platform(message):
    bot.reply_to(
        message,
        "🎥 **Select a platform:**",
        reply_markup=video_menu(),
        parse_mode="Markdown"
    )

# Handle video platform selection
@bot.message_handler(func=lambda message: message.text in ["📹 YouTube", "🎵 TikTok"])
def ask_for_video_link(message):
    platform = message.text
    bot.reply_to(
        message,
        f"📥 Send me the link for the {platform} video you'd like to download.",
        parse_mode="Markdown"
    )

# Download video logic using yt-dlp
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def download_video(message):
    url = message.text
    bot.reply_to(message, "⏳ Downloading your video, please wait...")
    try:
        ydl_opts = {
            'outtmpl': f'{TEMP_DIR}/%(title)s.%(ext)s',
            'format': 'best'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
        
        with open(file_path, "rb") as video:
            bot.send_video(message.chat.id, video)
        
        cleanup_temp_files()
    except yt_dlp.DownloadError:
        bot.reply_to(message, "❌ **Failed to download the video.**\nPlease check the link or try again later.")
    except Exception as e:
        bot.reply_to(message, "❌ **An unexpected error occurred.**\nPlease try again later.")
        print(f"Error: {e}")

# Handle "Convert Image" button
@bot.message_handler(func=lambda message: message.text == "🖼️ Convert Image")
def select_image_format(message):
    bot.reply_to(
        message,
        "🖼️ **Select the format to convert your image into:**",
        reply_markup=image_conversion_menu(),
        parse_mode="Markdown"
    )

# Image conversion logic
@bot.message_handler(content_types=["photo"])
def handle_image_upload(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    file_path = file_info.file_path
    downloaded_file = bot.download_file(file_path)

    input_file = os.path.join(TEMP_DIR, "input_image")
    with open(input_file, "wb") as file:
        file.write(downloaded_file)
    
    bot.reply_to(message, "📥 Image uploaded. Now select the format to convert into.", reply_markup=image_conversion_menu())

@bot.message_handler(func=lambda message: message.text in ["📷 JPG", "🖼️ PNG", "📜 PDF"])
def convert_image(message):
    format_map = {
        "📷 JPG": "JPEG",
        "🖼️ PNG": "PNG",
        "📜 PDF": "PDF"
    }
    output_format = format_map[message.text]
    input_file = os.path.join(TEMP_DIR, "input_image")
    
    if not os.path.exists(input_file):
        bot.reply_to(message, "❌ **No image uploaded.** Please upload an image first.")
        return
    
    try:
        with Image.open(input_file) as img:
            output_file = os.path.join(TEMP_DIR, f"converted_image.{output_format.lower()}")
            img.save(output_file, output_format)

        with open(output_file, "rb") as file:
            bot.send_document(message.chat.id, file)
        
        cleanup_temp_files()
    except Exception as e:
        bot.reply_to(message, "❌ **Failed to convert the image.**\nPlease try again.")
        print(f"Error: {e}")

# Handle "Back" button
@bot.message_handler(func=lambda message: message.text == "🔙 Back")
def go_back_to_main_menu(message):
    bot.reply_to(message, "🔙 Back to the main menu.", reply_markup=main_menu())

# Run the bot
print("Bot is running...")
bot.polling()
