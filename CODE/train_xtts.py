"""
train_xtts.py
Fine-tunes XTTS-v2's GPT component on your corrected, denoised English
dataset (95 clips: 80 original scripted sentences + 15 common phrases).

Starts from the base pretrained XTTS-v2 checkpoint (already cached
locally), not from the old finetuned_model/male/best_model.pth -- that
earlier checkpoint was trained on a dataset with known label-mismatch
corruption (see project history), so we retrain fresh rather than
continuing from it.

Calibrated conservatively for 8GB RAM: batch size 1, heavy gradient
accumulation to simulate a larger effective batch, short max audio
length to bound memory use per sample.

Usage:
    python train_xtts.py
"""

import os
from trainer import Trainer, TrainerArgs
from TTS.tts.datasets import load_tts_samples
from TTS.tts.configs.shared_configs import BaseDatasetConfig
from TTS.tts.layers.xtts.trainer.gpt_trainer import GPTTrainer, GPTTrainerConfig, GPTArgs
from TTS.tts.configs.xtts_config import XttsAudioConfig

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

XTTS_CACHE_DIR = os.path.expanduser(
    "~/Library/Application Support/tts/tts_models--multilingual--multi-dataset--xtts_v2"
)
DVAE_CHECKPOINT = os.path.join(XTTS_CACHE_DIR, "dvae.pth")
MEL_NORM_FILE = os.path.join(XTTS_CACHE_DIR, "mel_stats.pth")
TOKENIZER_FILE = os.path.join(XTTS_CACHE_DIR, "vocab.json")
XTTS_CHECKPOINT = os.path.join(XTTS_CACHE_DIR, "model.pth")
XTTS_CONFIG_FILE = os.path.join(XTTS_CACHE_DIR, "config.json")

OUTPUT_PATH = os.path.join(PROJECT_ROOT, "xtts_training_output")
DATASET_PATH = os.path.join(PROJECT_ROOT, "finetune_dataset", "male")

RUN_NAME = "echogenesis_male_en"
NUM_EPOCHS = 30
BATCH_SIZE = 1
GRAD_ACCUM_STEPS = 16
MAX_AUDIO_LEN_SECONDS = 11
LEARNING_RATE = 5e-6


def main():
    config_dataset = BaseDatasetConfig(
        formatter="coqui",
        dataset_name="echogenesis_male",
        path=DATASET_PATH,
        meta_file_train="metadata_train.csv",
        meta_file_val="metadata_eval.csv",
        language="en",
    )

    model_args = GPTArgs(
        max_conditioning_length=132300,
        min_conditioning_length=66150,
        max_wav_length=MAX_AUDIO_LEN_SECONDS * 22050,
        max_text_length=200,
        mel_norm_file=MEL_NORM_FILE,
        dvae_checkpoint=DVAE_CHECKPOINT,
        xtts_checkpoint=XTTS_CHECKPOINT,
        tokenizer_file=TOKENIZER_FILE,
        gpt_num_audio_tokens=1026,
        gpt_start_audio_token=1024,
        gpt_stop_audio_token=1025,
        gpt_use_masking_gt_prompt_approach=True,
        gpt_use_perceiver_resampler=True,
    )

    audio_config = XttsAudioConfig(sample_rate=22050, dvae_sample_rate=22050, output_sample_rate=24000)

    config = GPTTrainerConfig(
        output_path=OUTPUT_PATH,
        model_args=model_args,
        run_name=RUN_NAME,
        project_name="EchoGenesis",
        audio=audio_config,
        batch_size=BATCH_SIZE,
        batch_group_size=0,
        eval_batch_size=BATCH_SIZE,
        num_loader_workers=2,
        eval_split_max_size=256,
        print_step=5,
        plot_step=50,
        log_model_step=50,
        save_step=100,
        save_n_checkpoints=2,
        save_checkpoints=True,
        print_eval=True,
        optimizer="AdamW",
        optimizer_wd_only_on_weights=True,
        optimizer_params={"betas": [0.9, 0.96], "eps": 1e-8, "weight_decay": 1e-2},
        lr=LEARNING_RATE,
        lr_scheduler="MultiStepLR",
        lr_scheduler_params={"milestones": [50000, 150000, 300000], "gamma": 0.5, "last_epoch": -1},
        epochs=NUM_EPOCHS,
        grad_clip=0.5,
        test_sentences=[],
    )

    model = GPTTrainer.init_from_config(config)

    train_samples, eval_samples = load_tts_samples(
        [config_dataset],
        eval_split=True,
        eval_split_max_size=config.eval_split_max_size,
        eval_split_size=0.1,
    )

    trainer = Trainer(
        TrainerArgs(
            restore_path=None,
            skip_train_epoch=False,
            start_with_eval=False,
            grad_accum_steps=GRAD_ACCUM_STEPS,
        ),
        config,
        output_path=OUTPUT_PATH,
        model=model,
        train_samples=train_samples,
        eval_samples=eval_samples,
    )
    trainer.fit()


if __name__ == "__main__":
    main()
