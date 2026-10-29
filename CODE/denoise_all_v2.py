import noisereduce as nr
import soundfile as sf
from pathlib import Path
import shutil

FOLDERS = [
    "finetune_dataset/male/wavs",
    "finetune_dataset/male/tamil_casual/wavs",
    "finetune_dataset/male/tamil_formal/wavs",
]

for folder in FOLDERS:
    src_dir = Path(folder)
    backup_dir = src_dir.parent / (src_dir.name + "_pre_denoise_backup")

    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    wav_files = sorted(src_dir.glob("prompt_*.wav"))
    print(f"\nDenoising {len(wav_files)} files in {folder}...")

    shutil.copytree(src_dir, backup_dir)
    print(f"  Backed up originals to {backup_dir}")

    for wav in wav_files:
        data, rate = sf.read(str(wav))
        reduced = nr.reduce_noise(
            y=data, sr=rate,
            stationary=False,       # adapts to continuous hum better than a fixed profile
            prop_decrease=1.0,      # maximum reduction
            n_std_thresh_stationary=1.2,
        )
        sf.write(str(wav), reduced, rate)

    print(f"  Denoised {len(wav_files)} files in place: {folder}")

print("\nDone.")
