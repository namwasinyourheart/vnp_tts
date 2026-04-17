
import os

from hydra import initialize, compose
from omegaconf import OmegaConf

from src.utils.log_utils import setup_logger
from src.utils.exp_utils import create_exp_dir, setup_environment
from src.utils.data_utils import create_REMOVEDds
from datasets import load_from_disk
from datasets import Dataset, DatasetDict

from src.utils.data_utils import make_splits, create_REMOVEDds

from transformers import set_seed
import warnings

from typing import Callable, Dict, List


warnings.filterwarnings("ignore")

logger = setup_logger(__name__)


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Load generation config.")
    parser.add_argument(
        "--config_path",
        type=str,
        required=True,
        help="Path to the YAML config file for generating.",
    )
    args, override_args = parser.parse_known_args()
    return args, override_args


def load_cfg(config_path: str, override_args: List[str] = None):
    """
    Load a configuration file using Hydra and OmegaConf.

    Returns:
        (cfg, exp_args, data_args, model_args, train_args, eval_args, gen_args, device_args)
    """
    override_args = override_args or []
    config_path = os.path.normpath(config_path)

    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    config_dir = os.path.dirname(config_path)
    config_fn = os.path.splitext(os.path.basename(config_path))[0]

    try:
        with initialize(version_base=None, config_path=config_dir):
            cfg = compose(config_name=config_fn, overrides=override_args)
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration from {config_path}: {e}")

    exp_args = cfg.exp_manager
    data_args = cfg.data
    model_args = cfg.model
    train_args = cfg.train
    eval_args = cfg.evaluate
    device_args = cfg.device
    gen_args = cfg.generate

    return cfg, exp_args, data_args, model_args, train_args, eval_args, gen_args, device_args


def save_cfg(cfg, config_path: str):
    OmegaConf.save(cfg, config_path)
    logger.info(f"Configuration saved to {config_path}")


def preprocess_sample(sample, tokenizer, max_len, g2p):

    # get special tokens
    speech_gen_start = tokenizer.convert_tokens_to_ids("<|SPEECH_GENERATION_START|>")
    ignore_index = -100  # this is from LLaMA

    # unpack sample
    vq_codes = sample["codes"]
    text = sample["text"]

    # phonemize
    phones = g2p.phonemize([text])

    # SAFE CHECK
    if not phones or not phones[0]:
        LOGGER.warning(f"⚠️ Empty phonemization output for sample: {sample['__key__']} text={text}")
        return None

    phones = phones[0].split()
    phones = " ".join(phones)

    codes_str = "".join([f"<|speech_{i}|>" for i in vq_codes])

    # get chat format
    chat = f"""user: Convert the text to speech:<|TEXT_PROMPT_START|>{phones}<|TEXT_PROMPT_END|>\nassistant:<|SPEECH_GENERATION_START|>{codes_str}<|SPEECH_GENERATION_END|>"""  # noqa
    ids = tokenizer.encode(chat)

    # pad to make seq len
    if len(ids) < max_len:
        ids = ids + [tokenizer.pad_token_id] * (max_len - len(ids))
    else:
        ids = ids[:max_len]

    # convert to tensor
    input_ids = torch.tensor(ids, dtype=torch.long)

    labels = torch.full_like(input_ids, ignore_index)
    speech_gen_start_idx = (input_ids == speech_gen_start).nonzero(as_tuple=True)[0]
    if len(speech_gen_start_idx) > 0:
        speech_gen_start_idx = speech_gen_start_idx[0]
        labels[speech_gen_start_idx:] = input_ids[speech_gen_start_idx:]

    # create attention mask
    attention_mask = (input_ids != tokenizer.pad_token_id).long()

    # return in hf format
    return {
        "input_ids": input_ids,
        "labels": labels,
        "attention_mask": attention_mask,
    }


    
def process_dataset(
    dataset: DatasetDict,
    data_args
):
    from neucodec import NeuCodec

    model = NeuCodec.from_pretrained("neuphonic/neucodec")
    model.eval().cuda()

    # ds = load_from_disk()

    # Prepare audio codes
    dataset_codec = dataset.map(
        get_audio_codes_batched,
        fn_kwargs={"model": model},
        batched=True,
        # batch_size=1000,
        desc="Add NeuCodec codes"
    )

    dataset_codec.save_to_disk("ds_codec")


import torch

def get_audio_codes(example, model):
    audio = example["audio"]["array"]

    # (T,) -> (1, 1, T)
    y = torch.from_numpy(audio).float().unsqueeze(0).unsqueeze(0).cuda()

    with torch.no_grad():
        codes = model.encode_code(y)

    return {
        "codes": codes.flatten().cpu().tolist()
    }

import torch

def get_audio_codes_batched(examples, model):
    """
    Encode từng audio riêng lẻ, rồi append codes vào list
    """

    all_codes = []

    for audio in examples["audio"]:
        # (T,) -> (1, 1, T)
        y = (
            torch.from_numpy(audio["array"])
            .float()
            .unsqueeze(0)
            .unsqueeze(0)
            .cuda()
        )

        with torch.no_grad():
            codes = model.encode_code(y)

        # remove batch dim, flatten
        codes = codes.squeeze(0).flatten().cpu().tolist()
        all_codes.append(codes)

    return {
        "codes": all_codes
    }



def prepare_data(exp_args, data_args, model_args):
    root_data_dir = data_args.root_data_dir
    REMOVEDraw_data_dir = getattr(data_args, "REMOVEDraw_data_dir", os.path.join(root_data_dir, "raw", "hf"))
    exps_data_dir = getattr(data_args, "exps_data_dir", os.path.join(root_data_dir, "exps"))
    prepared_data_dir = (
        data_args.prepared_data_dir
        or os.path.join(exps_data_dir, f"{exp_args.exp_name}__{exp_args.exp_variant}")
    )

    logger.info(f"prepared_data_dir: {prepared_data_dir}")

    if not os.path.exists(prepared_data_dir) or data_args.continue_prep:
        logger.info("Preparing dataset...")

        if os.path.exists(REMOVEDraw_data_dir) and data_args.use_existing_hfds:
            logger.info(f"Loading existing HF dataset from disk {REMOVEDraw_data_dir}")
            dataset = load_from_disk(REMOVEDraw_data_dir)

            dataset = ensure_datasetdict(dataset)

            if data_args.only_load_test_split:
                dataset = DatasetDict({"test": dataset["test"]})
        else:
            logger.info("Creating new HF dataset...")
            dataset = create_REMOVEDds(
                dataset_script_path=data_args.dataset_script_path,
                data_dir=data_args.dataset_source_dir,
                subset_names=data_args.subset_names,
                save_dir=REMOVEDraw_data_dir if data_args.save_hfds else None,
            )


        if data_args.subset_ratio and 0 < data_args.subset_ratio < 1:
            logger.info(f"Subsetting dataset to {data_args.subset_ratio * 100}% of original size")
            dataset = DatasetDict({
                split: dataset[split].shuffle(seed=exp_args.seed).select(range(int(data_args.subset_ratio * len(dataset[split]))))
                for split in dataset.keys()
            })

        if "train" in dataset:
            logger.info("Shuffling training data")
            dataset["train"] = dataset["train"].shuffle(seed=exp_args.seed)


        # split
        if data_args.do_split:
            logger.info("Shuffling dataset before splitting")
            dataset = DatasetDict({
                split: dataset[split].shuffle(seed=exp_args.seed)
                for split in dataset.keys()
            })
            logger.info("Splitting dataset into train/val/test")
            dataset = make_splits(dataset, data_args.test_ratio, data_args.val_ratio, exp_args.seed)


        prepared_dataset = dataset

        logger.info(f"Saving prepared dataset to disk {prepared_data_dir}")
        prepared_dataset.save_to_disk(prepared_data_dir)
    else:

        logger.info("Loading prepared dataset from disk ...")
        prepared_dataset = load_from_disk(prepared_data_dir)

    if data_args.do_show:
        print(prepared_dataset)


    return prepared_dataset


if __name__ == "__main__":
    pass