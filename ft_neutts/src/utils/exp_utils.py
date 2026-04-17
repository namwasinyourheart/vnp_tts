
import os
from hydra import initialize, compose
from pathlib import Path
from omegaconf import OmegaConf

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Load generation config.")
    parser.add_argument("--config_path", type=str, required=True, help="Path to the YAML config file for generating.")

    args, override_args = parser.parse_known_args()
    return args, override_args


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



def print_cfg(yaml_path: str, node: str = None) -> None:
    cfg = OmegaConf.load(Path(yaml_path))
    if node:
        cfg = OmegaConf.select(cfg, node)
        if cfg is None:
            raise KeyError(f"Config node not found: {node}")
    print(OmegaConf.to_yaml(cfg, resolve=True))


def create_exp_dir(exp_name, exp_variant, exps_dir='exps', sub_dirs=['checkpoints', 'data', 'results']):
    """
    Create necessary directories for an experiment.
    
    Args:
        exp_name (str): Name of the experiment.
        sub_dirs (list): List of subdirectories to create.

    Returns:
        Tuple containing paths to experiment directories.
    """
    # os.makedirs("exps", exist_ok=True)
    os.makedirs(exps_dir, exist_ok=True)
    # exp_dir = os.path.join("exps", exp_name)
    exp_dir = os.path.join(exps_dir, exp_name)
    os.makedirs(exp_dir, exist_ok=True)

    exp_variant_dir = os.path.join(exp_dir, exp_variant)
    os.makedirs(exp_variant_dir, exist_ok=True)
    
    sub_dirs_paths = {sub_dir: os.path.join(exp_variant_dir, sub_dir) for sub_dir in sub_dirs}
    for path in sub_dirs_paths.values():
        os.makedirs(path, exist_ok=True)


    exp_variant_data_dir = sub_dirs_paths['data']
    exp_variant_checkpoints_dir = sub_dirs_paths['checkpoints']
    exp_variant_results_dir = sub_dirs_paths['results']
    
    return (exp_dir, exp_variant_dir, exp_variant_data_dir, exp_variant_checkpoints_dir, exp_variant_results_dir)


def setup_environment() -> None:
    from dotenv import load_dotenv
    _ = load_dotenv()

    from huggingface_hub import login
    login(token=os.environ['HUGGINGFACEHUB_API_TOKEN'])