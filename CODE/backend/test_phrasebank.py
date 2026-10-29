import tempfile, config
from pathlib import Path
config.PHRASE_BANK = Path(tempfile.mkdtemp())
import phrasebank
phrasebank.PHRASE_BANK = config.PHRASE_BANK
assert phrasebank.normalize("  How are YOU?! ") == "how are you"
assert phrasebank.normalize("नमस्ते, आप कैसे हैं?") == "नमस्ते आप कैसे हैं"
phrasebank.add("male", "en", "How are you?", b"RIFFfake")
assert phrasebank.lookup("male", "en", "how are you") is not None
assert phrasebank.lookup("male", "en", "how are you not") is None      # no fuzzy matching
assert phrasebank.lookup("female", "en", "how are you") is None          # per-voice
phrasebank.add("male", "en", "how are you", b"RIFFnew")                 # re-record overwrites
assert len(phrasebank.list_phrases("male", "en")) == 1
print("phrasebank tests passed")
