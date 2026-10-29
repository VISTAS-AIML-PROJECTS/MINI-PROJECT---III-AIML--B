import sys
import numpy as np
import soundfile as sf
from pathlib import Path

SRC_DIR = Path(sys.argv[1])
OUT_DIR = Path(sys.argv[2])
TARGET_RMS_DB = float(sys.argv[3]) if len(sys.argv) > 3 else -20.0
PEAK_LIMIT = 0.95  # never exceed this, avoids clipping

OUT_DIR.mkdir(parents=True, exist_ok=True)
wav_files = sorted(SRC_DIR.glob("prompt_*.wav"))
print(f"Normalizing {len(wav_files)} files to {TARGET_RMS_DB} dB RMS...\n")

for wav in wav_files:
    data, rate = sf.read(str(wav))
    rms = np.sqrt(np.mean(data ** 2))
    if rms < 1e-6:
        print(f"  {wav.name} -> SKIPPED (silent?)")
        continue
    gain = (10 ** (TARGET_RMS_DB / 20)) / rms
    out = data * gain
    peak = np.max(np.abs(out))
    if peak > PEAK_LIMIT:
        out = out * (PEAK_LIMIT / peak)
    sf.write(str(OUT_DIR / wav.name), out, rate, subtype="PCM_16")
    print(f"  {wav.name}: gain {20*np.log10(gain):+.1f} dB, peak {np.max(np.abs(out)):.2f}")

print(f"\nSaved to {OUT_DIR}/")
