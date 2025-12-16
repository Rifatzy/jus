from .id import LANG_ID
from .en import LANG_EN

LANGUAGES = {
    "id": LANG_ID,
    "en": LANG_EN
}

def get_text(key: str, lang: str = "id", **kwargs) -> str:
    """Get text in specified language"""
    texts = LANGUAGES.get(lang, LANG_ID)
    text = texts.get(key, LANG_ID.get(key, key))

    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text