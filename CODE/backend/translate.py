def translate(text: str, src: str, tgt: str) -> str:
    """Prototype translation via deep-translator (Google, no key).
    Swap for the official Google/DeepL API before real deployment."""
    if not tgt or src == tgt:
        return text
    from deep_translator import GoogleTranslator
    return GoogleTranslator(source=src or "auto", target=tgt).translate(text)
