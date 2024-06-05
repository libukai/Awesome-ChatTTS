import random
import numpy as np
import torch
import ChatTTS
import soundfile

chat = ChatTTS.Chat()
chat.load_models(compile=True)  # Set to True for better performance


def deterministic(seed):

    ###################################
    # Declare the seed.

    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    rand_spk = chat.sample_random_speaker()

    ###################################
    # Sample a speaker from Gaussian.

    params_infer_code = {
        'spk_emb': rand_spk,  # add sampled speaker
        'prompt': '[speed_2]',  # speed control
        'temperature': .3,  # using custom temperature
        'top_P': 0.7,  # top P decode
        'top_K': 20,  # top K decode
    }

    ###################################
    # For sentence level manual control.

    # use oral_(0-9), laugh_(0-2), break_(0-7)
    # to generate special token in text to synthesize.

    params_refine_text = {
        'prompt': f'[oral_4][laugh_0][break_2]'
    }

    return params_infer_code, params_refine_text


def generate_audio(seed=2):
    params_infer_code, params_refine_text = deterministic(seed)
    print(f"\nThe Seed is {seed}\n")
    text = '曾经有一份真挚的爱情摆在我的面前，但是我没有珍惜，等我失去后才后悔莫及，尘世间最痛苦的事情莫过于此。'
    wav = chat.infer(text, params_refine_text=params_refine_text,  params_infer_code=params_infer_code)
    soundfile.write(f"output{seed}.wav", wav[0][0], 24000)
    print(f"\nThe Wav{seed} saved.")


if __name__ == "__main__":
    generate_audio()
