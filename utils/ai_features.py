import os
import aiohttp
import asyncio
from typing import Optional, Dict, List
from dataclasses import dataclass
import json
import re

# Try import openai
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class AIResponse:
    success: bool
    content: str = ""
    error: str = ""


class AIFeatures:
    """AI Features using OpenAI API"""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.enabled = bool(api_key) and OPENAI_AVAILABLE

        if self.enabled and OPENAI_AVAILABLE:
            openai.api_key = api_key

    async def chat(self, message: str, context: str = "") -> AIResponse:
        """AI Chatbot - General conversation"""
        if not self.enabled:
            return AIResponse(success=False, error="AI not enabled")

        try:
            system_prompt = """Kamu adalah asisten bot Telegram yang ramah dan membantu.
Kamu bisa menjawab pertanyaan umum, memberikan saran, dan membantu pengguna.
Jawab dengan singkat, jelas, dan dalam bahasa yang sama dengan user.
Jika ditanya tentang download video, jelaskan cara menggunakan bot ini."""

            if context:
                system_prompt += f"\n\nKonteks tambahan: {context}"

            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=500,
                temperature=0.7
            )

            content = response.choices[0].message.content
            return AIResponse(success=True, content=content)

        except Exception as e:
            return AIResponse(success=False, error=str(e))

    async def generate_caption(self, title: str, author: str, platform: str) -> AIResponse:
        """Generate creative caption for downloaded content"""
        if not self.enabled:
            return AIResponse(success=False, error="AI not enabled")

        try:
            prompt = f"""Buatkan caption singkat dan menarik untuk konten ini:
Judul: {title}
Author: {author}
Platform: {platform}

Buat caption yang:
- Singkat (1-2 kalimat)
- Menarik dan catchy
- Bisa include emoji yang relevan
- Dalam bahasa Indonesia"""

            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.8
            )

            content = response.choices[0].message.content
            return AIResponse(success=True, content=content)

        except Exception as e:
            return AIResponse(success=False, error=str(e))

    async def translate(self, text: str, target_lang: str = "en") -> AIResponse:
        """Translate text to target language"""
        if not self.enabled:
            return AIResponse(success=False, error="AI not enabled")

        lang_names = {
            "en": "English",
            "id": "Indonesian",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi",
            "pt": "Portuguese",
            "ru": "Russian",
        }

        target = lang_names.get(target_lang, "English")

        try:
            prompt = f"Translate the following text to {target}. Only provide the translation, nothing else:\n\n{text}"

            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )

            content = response.choices[0].message.content
            return AIResponse(success=True, content=content)

        except Exception as e:
            return AIResponse(success=False, error=str(e))

    async def summarize(self, text: str) -> AIResponse:
        """Summarize long text"""
        if not self.enabled:
            return AIResponse(success=False, error="AI not enabled")

        try:
            prompt = f"""Ringkas teks berikut dalam 2-3 kalimat singkat:

{text}

Berikan ringkasan yang padat dan informatif."""

            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.5
            )

            content = response.choices[0].message.content
            return AIResponse(success=True, content=content)

        except Exception as e:
            return AIResponse(success=False, error=str(e))

    async def detect_content_type(self, text: str) -> AIResponse:
        """Detect content type/category from text"""
        if not self.enabled:
            return AIResponse(success=False, error="AI not enabled")

        try:
            prompt = f"""Kategorikan konten berikut ke salah satu kategori:
- music (musik/lagu)
- comedy (komedi/lucu)
- education (edukasi/tutorial)
- entertainment (hiburan)
- sports (olahraga)
- news (berita)
- gaming (game)
- food (makanan)
- fashion (fashion/beauty)
- other (lainnya)

Teks: {text}

Jawab hanya dengan satu kata kategori saja."""

            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=20,
                temperature=0.3
            )

            content = response.choices[0].message.content.strip().lower()
            return AIResponse(success=True, content=content)

        except Exception as e:
            return AIResponse(success=False, error=str(e))

    async def generate_hashtags(self, title: str, platform: str) -> AIResponse:
        """Generate relevant hashtags"""
        if not self.enabled:
            return AIResponse(success=False, error="AI not enabled")

        try:
            prompt = f"""Buatkan 5 hashtag yang relevan untuk konten ini:
Judul: {title}
Platform: {platform}

Format: #hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5
Gunakan hashtag yang populer dan relevan."""

            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )

            content = response.choices[0].message.content
            return AIResponse(success=True, content=content)

        except Exception as e:
            return AIResponse(success=False, error=str(e))

    async def ask_question(self, question: str) -> AIResponse:
        """Answer general questions"""
        if not self.enabled:
            return AIResponse(success=False, error="AI not enabled")

        try:
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Kamu adalah asisten yang membantu dan memberikan jawaban akurat. Jawab dengan singkat dan jelas."},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0.7
            )

            content = response.choices[0].message.content
            return AIResponse(success=True, content=content)

        except Exception as e:
            return AIResponse(success=False, error=str(e))


# Alternative AI using free APIs
class FreeAI:
    """Free AI alternatives without API key"""

    def __init__(self):
        self.session = None

    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def translate_free(self, text: str, target: str = "en", source: str = "auto") -> AIResponse:
        """Free translation using Google Translate API (unofficial)"""
        try:
            session = await self._get_session()

            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": source,
                "tl": target,
                "dt": "t",
                "q": text
            }

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    translated = "".join([item[0] for item in data[0] if item[0]])
                    return AIResponse(success=True, content=translated)

            return AIResponse(success=False, error="Translation failed")

        except Exception as e:
            return AIResponse(success=False, error=str(e))

    async def close(self):
        if self.session:
            await self.session.close()


# Singleton instances
def get_ai_features():
    try:
        from config import Config
        return AIFeatures(Config.OPENAI_API_KEY)
    except:
        return AIFeatures("")

ai_features = get_ai_features()
free_ai = FreeAI()