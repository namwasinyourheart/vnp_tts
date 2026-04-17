
from datasets import DatasetDict, concatenate_datasets
from typing import Union, List

from tqdm import tqdm
import re
import requests

def get_data_subset(dataset, subset_size, seed):
    """
    Get a subset of a Hugging Face Dataset or DatasetDict using either
    an absolute number of samples or a ratio.

    Args:
        subset_size (int | float): number of samples or ratio (0 < ratio <= 1)
        dataset: a Dataset or DatasetDict
        seed (int): random seed for shuffling

    Returns:
        Dataset or DatasetDict: subset of the input dataset
    """
    from datasets import DatasetDict

    def _subset_split(ds_split):
        # Determine number of samples
        if isinstance(subset_size, float):
            if not (0 < subset_size <= 1):
                raise ValueError("Ratio must be between 0 and 1.")
            n_samples = int(len(ds_split) * subset_size)
        else:
            n_samples = subset_size

        if n_samples == -1 or n_samples >= len(ds_split):
            return ds_split
        return ds_split.shuffle(seed=seed).select(range(n_samples))

    # Handle DatasetDict
    if isinstance(dataset, DatasetDict):
        return DatasetDict({split: _subset_split(ds_split) for split, ds_split in dataset.items()})
    else:
        return _subset_split(dataset)

def create_REMOVEDds(
    dataset_script_path: str,
    data_dir: str,
    subset_names: Union[str, List[str]],
    save_dir: str = None,
    streaming: bool = False,
) -> DatasetDict:
    """
    Create a Hugging Face dataset (support multiple subsets) from a local dataset script.
    If multiple subset names are provided, they will be concatenated into one dataset.
    """
    # Đảm bảo subset_names luôn là list
    if isinstance(subset_names, str):
        subset_names = [subset_names]

    datasets_list = []
    for name in subset_names:
        ds = load_dataset(
            path=dataset_script_path,
            data_dir=data_dir,
            name=name,
            trust_remote_code=True,
            download_mode="force_redownload",
            streaming=streaming,
        )
        datasets_list.append(ds)

    # Gộp nhiều subset lại
    if len(datasets_list) == 1:
        merged_ds = datasets_list[0]
    else:
        # Nếu là DatasetDict (nhiều split), cần gộp từng split riêng
        if isinstance(datasets_list[0], DatasetDict):
            merged_ds = DatasetDict()
            for split in datasets_list[0].keys():
                merged_ds[split] = concatenate_datasets(
                    [d[split] for d in datasets_list if split in d]
                )
        else:
            merged_ds = concatenate_datasets(datasets_list)

    if not streaming and save_dir:
        merged_ds.save_to_disk(save_dir)

    return merged_ds
def make_splits(
    dataset: DatasetDict, 
    test_size=0.1, 
    dev_size=0.1, 
    seed=42
) -> DatasetDict:
    """
    Ensure train/dev/test splits exist. If no 'test' split, create one from train.
    """
    if "test" not in dataset:
        split = dataset["train"].train_test_split(test_size=test_size, seed=seed)
        train_data = split["train"]
        test_data = split["test"]
    else:
        train_data = dataset["train"]
        test_data = dataset["test"]

    train_dev = train_data.train_test_split(test_size=dev_size, seed=seed)
    return DatasetDict({"train": train_dev["train"], "dev": train_dev["test"], "test": test_data})


from tqdm import tqdm

def build_sid2idx(
    dataset: Dataset, 
    sid_col="sid"
):
    """
    Build a mapping from `sid` to dataset index for a HuggingFace Dataset.

    This function iterates over the specified `sid` column and creates a
    dictionary mapping each unique sid to its integer index in the dataset.

    Parameters
    ----------
    dataset : datasets.Dataset
        HuggingFace Dataset object.
    sid_col : str, optional
        Name of the column containing sample IDs (default: "sid").

    Returns
    -------
    dict
        A dictionary mapping `sid -> index`.

    Notes
    -----
    - Assumes `sid` values are unique.
    - Suitable for large datasets; progress is shown via tqdm.
    - Avoids copying heavy fields (e.g., audio) into memory.
    """
    return {
        sid: i
        for i, sid in enumerate(
            tqdm(dataset[sid_col], desc=f"Building {sid_col}→index map")
        )
    }


def add_sample_id(
    dataset: Dataset, 
    start=0, 
    prefix=None, 
    width=0, 
    column_name="sid"
):
    """
    Add sample_id column to a HuggingFace Dataset.

    dataset     : datasets.Dataset
    start       : starting id
    prefix      : optional prefix (e.g. 's')
    width       : zero-padding width
    column_name : name of id column (default 'sid')
    """
    def format_sid(i):
        if width > 0:
            num = f"{i:0{width}d}"
        else:
            num = str(i)

        return f"{prefix}{num}" if prefix else num

    sids = [format_sid(i) for i in range(start, start + len(dataset))]
    return dataset.add_column(column_name, sids)

import requests
from typing import List, Dict, Union


def is_vietnamese_word_via_api(
    words: Union[str, List[str]],
    base_url="https://ed3e-14-232-225-131.ngrok-free.app/asr/v1/is_vietnamese_word",
    timeout=5,
) -> Dict[str, bool] | None:
    """
    Check Vietnamese word(s) using external API.

    words   : str | List[str]
    return  : Dict[str, bool] | None (None nếu lỗi)
    """
    try:
        payload = {
            "words": words
        }

        resp = requests.post(
            base_url,
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()

        data = resp.json()
        # expected:
        # {
        #   "results": {
        #       "chào": true,
        #       "hello": false
        #   }
        # }

        return data["results"]

    except Exception as e:
        print(f"Failed to check words '{words}': {e}")
        return None


def has_special_char(text):
    return bool(re.search(r"[^a-zA-ZÀ-ỹ0-9\s]", text))



# def has_special_char(text):
#     return bool(re.search(r"[^a-zA-Z0-9]", text))




def find_special_chars_in_texts(texts):
    """
    texts: list[str]
    return: sorted list of unique special chara
    cters
    """
    # Cho phép chữ Latin + chữ có dấu VN + số + space
    pattern = re.compile(r"[^a-zA-ZÀ-ỹ0-9\s]")

    specials = set()
    iterator = tqdm(texts, desc="Finding special characters...")

    for t in iterator:
        specials.update(pattern.findall(t))

    return sorted(specials)


from typing import List, Dict, Callable
from tqdm import tqdm


def find_non_vietnamese_words(
    words: List[str],
    check_vietnamese_batch: Callable[[List[str]], Dict[str, bool]],
    batch_size: int = 10000,
) -> List[str]:
    """
    Find non-Vietnamese words using a batch checker with local cache.

    Args:
        words: List of words to check
        check_vietnamese_batch: function(List[str]) -> Dict[str, bool]
        batch_size: number of words per batch request

    Returns:
        Sorted list of non-Vietnamese words
    """
    cache: Dict[str, bool] = {}
    non_vn_words = set()

    # deduplicate upfront
    unique_words = list(set(words))

    # words not yet checked
    uncached_words = unique_words

    # batch checking
    for start in tqdm(
        range(0, len(uncached_words), batch_size),
        desc="Checking Vietnamese words",
    ):
        batch = uncached_words[start : start + batch_size]
        if not batch:
            continue

        result = check_vietnamese_batch(batch)
        # result: Dict[str, bool]
        cache.update(result)

    # collect non-Vietnamese words
    for word in unique_words:
        if not cache.get(word, False):
            non_vn_words.add(word)

    return sorted(non_vn_words)


from collections import Counter
from typing import Dict, Any
from datasets import Dataset
from tqdm import tqdm


def REMOVEDcolumn_value_counts(
    dataset: Dataset,
    column: str,
) -> Dict[Any, int]:
    """
    Get unique values and their counts for a dataset column.

    Args:
        dataset: Hugging Face Dataset
        column: column name

    Returns:
        Dict[value, count]
    """
    counter = Counter()

    for row in tqdm(dataset, desc=f"Counting '{column}'"):
        counter[row[column]] += 1

    return dict(counter)


from collections import Counter


def REMOVEDcolumn_value_counts_fast(
    dataset: Dataset,
    column: str,
):
    return dict(Counter(dataset[column]))
