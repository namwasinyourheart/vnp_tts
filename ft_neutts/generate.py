# import sys
# sys.path.append("/home/nampv1/projects/tts/vnp_tts/ft_neutts/neutts")

from src.utils.exp_utils import parse_args, setup_environment
import os
from hydra import initialize, compose
from omegaconf import OmegaConf
import soundfile as sf

import time

from src.utils.log_utils import setup_logger

logger = setup_logger()


def load_cfg(config_path, override_args=None):

    """
    Load a configuration file using Hydra and OmegaConf.
    
    Args:
        config_path (str): Path to the configuration file.
        override_args (list, optional): List of arguments to override configuration values.

    Returns:
        cfg: Loaded configuration object.
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

    return cfg


def load_model(model_args, device_args):

    if model_args.architecture == 'neutts':
        from neutts import NeuTTS
        model = NeuTTS(
            model_args=model_args,
            device_args=device_args,
            backbone_repo = model_args.pretrained_model_name_or_path,
            backbone_device = "cpu" if device_args.use_cpu else "cuda",
            codec_repo="neuphonic/neucodec",
            codec_device = "cpu" if device_args.use_cpu else "cuda",
        
        )
    else:
        raise ValueError(f"Currently only support NeuTTS architecture")

    return model

def generate_audio(model_args, device_args, input_args):
    logger.info("Loading model...")
    model = load_model(model_args, device_args)

    start_time = time.time()

    if model_args.architecture == 'neutts':

        ref_text = input_args.ref_text

        if input_args.ref_text and os.path.exists(input_args.ref_text):
            with open(input_args.ref_text, "r") as f:
                ref_text = f.read().strip()
                
            
        logger.info("Encoding reference audio...")
        ref_codes = model.encode_reference(input_args.ref_audio_path)


        logger.info("Generating audio...")
        audio = model.infer(input_args.text, ref_codes, ref_text)

        output_audio_name = f"{input_args.text.replace(' ', '_')[:30].lower()}.wav"

        logger.info(f"Saving audio to {os.path.join(input_args.output_dir, output_audio_name)}")
        sf.write(os.path.join(input_args.output_dir, output_audio_name), audio, 24000)

        logger.info(f"Generated audio in {time.time() - start_time:.2f} seconds")

    else:
        raise ValueError(f"Currently only support NeuTTS architecture")

    return audio

if __name__ == "__main__":

    # Setup environment
    setup_environment()

    # Parse arguments
    args, override_args = parse_args()

    # Load the generation config file
    cfg = load_cfg(args.config_path, override_args)

    print(OmegaConf.to_yaml(cfg))

    generate_audio(cfg.model, cfg.device, cfg.inputs)

    
    
    