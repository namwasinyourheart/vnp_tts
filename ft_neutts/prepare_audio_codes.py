from datasets import load_dataset

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



if __name__ == "__main__":

    from neucodec import NeuCodec

    model = NeuCodec.from_pretrained("neuphonic/neucodec")
    model.eval().cuda()

    dataset_name = "vivos"
    dataset = load_dataset(dataset_name)

    dataset_codec = dataset.map(
        get_audio_codes_batched,
        fn_kwargs={"model": model},
        batched=True,
        # batch_size=1000,
        desc="Add NeuCodec codes"
    )

    dataset_codec.save_to_disk(f"/media/nampv1/hdd/data/tts/ft_neutts/{dataset_name}_codec")

