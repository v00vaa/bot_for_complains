import re


SPACE_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[^а-яa-z0-9 ]", re.IGNORECASE)


def normalize(text: str) -> str:
    text = text.lower()

    text = text.replace("ё", "е")

    text = PUNCT_RE.sub(" ", text)

    text = SPACE_RE.sub(" ", text)

    return text.strip()
