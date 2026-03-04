from __future__ import annotations

import io
import sqlite3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from aiogram import Bot
from aiogram.types import FSInputFile

STORAGE_DIR = Path("storage")
BANNERS_DIR = STORAGE_DIR / "banners"
FONTS_DIR = STORAGE_DIR / "fonts"
CACHE_DB = STORAGE_DIR / "banners_cache.db"

BANNERS_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)

def _init_db() -> None:
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS banners_cache (
                bot_id INTEGER,
                filename TEXT,
                file_id TEXT,
                PRIMARY KEY (bot_id, filename)
            )
        """)

_init_db()

async def get_static_banner(bot: Bot, filename: str) -> str | None:
    file_path = BANNERS_DIR / filename
    if not file_path.exists():
        return None

    bot_id = bot.id
    
    with sqlite3.connect(CACHE_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_id FROM banners_cache WHERE bot_id = ? AND filename = ?", 
            (bot_id, filename)
        )
        row = cursor.fetchone()
        if row:
            return row[0]

    msg = await bot.send_photo(
        chat_id=bot_id, 
        photo=FSInputFile(file_path),
        disable_notification=True
    )
    file_id = msg.photo[-1].file_id
    await msg.delete()

    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO banners_cache (bot_id, filename, file_id) VALUES (?, ?, ?)",
            (bot_id, filename, file_id)
        )

    return file_id

async def preload_all_banners(bot: Bot) -> None:
    for file in BANNERS_DIR.glob("*.png"):
        if not file.name.startswith("tpl_"):
            await get_static_banner(bot, file.name)

def create_dynamic_banner(template_name: str, title: str, text: str) -> bytes:
    template_path = BANNERS_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template {template_name} not found in {BANNERS_DIR}")

    base = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(base)

    try:
        font_title = ImageFont.truetype(str(FONTS_DIR / "Inter-Black.ttf"), 72)
        font_sub = ImageFont.truetype(str(FONTS_DIR / "Inter-SemiBold.ttf"), 32)
    except IOError:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    line_img = Image.new("RGBA", base.size, (0, 0, 0, 0))
    line_draw = ImageDraw.Draw(line_img)
    line_draw.rectangle([80, 160, 130, 166], fill=(0, 180, 255, 255))
    line_img = line_img.filter(ImageFilter.GaussianBlur(4))
    base.alpha_composite(line_img)

    draw.text((76, 180), title, font=font_title, fill=(255, 255, 255, 255))
    
    y_offset = 275
    for line in text.split('\n')[:3]:
        draw.text((80, y_offset), line, font=font_sub, fill=(156, 163, 175, 255))
        y_offset += 42

    bio = io.BytesIO()
    base.save(bio, format="PNG")
    return bio.getvalue()
