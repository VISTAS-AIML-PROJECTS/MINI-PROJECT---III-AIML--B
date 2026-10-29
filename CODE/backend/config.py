import os
from pathlib import Path

# Drop this backend/ folder inside your echogenesis project root.
ROOT = Path(os.environ.get("ECHO_ROOT", Path(__file__).resolve().parent.parent))
PHRASE_BANK = ROOT / "phrase_bank"
CACHE_DIR = ROOT / "cache"
API_KEY = os.environ.get("ECHO_API_KEY", "")  # set this before exposing the server

# Languages XTTS-v2 can synthesize
XTTS_LANGS = {"en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl",
              "cs", "ar", "zh-cn", "ja", "hu", "ko", "hi"}

# Per-voice model setup. A checkpoint_dir is used only if it holds
# best_model.pth, config.json and vocab.json; otherwise base XTTS-v2 is used.
VOICES = {
    "male": {
        "checkpoint_dir": ROOT / "finetuned_model" / "male",
        "reference_dir": ROOT / "finetune_dataset" / "male" / "wavs",
    },
    "female": {  # zero-shot for now; point checkpoint_dir at her fine-tune later
        "checkpoint_dir": ROOT / "finetuned_model" / "female",
        "reference_dir": ROOT / "finetune_dataset" / "female" / "wavs",
    },
}
N_REFERENCE_CLIPS = 6
MAX_CHUNK_CHARS = 200
