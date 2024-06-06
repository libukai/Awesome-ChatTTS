import random
import numpy as np
import torch
import ChatTTS
import torchaudio

# 下载离线模型并加载

from modelscope import snapshot_download
model_dir = snapshot_download('pzc163/chatTTS')

chat = ChatTTS.Chat()
chat.load_models(source='local', local_path=model_dir, compile=True)


def deterministic(seed):

    # 配置随机种子，生成对应音色

    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    rand_spk = chat.sample_random_speaker()

    # 生成音频参数，详见 Readme 文档

    params_infer_code = {
        'spk_emb': rand_spk,  # add sampled speaker
        'prompt': '[speed_2]',  # speed control
        'temperature': .3,  # using custom temperature
        'top_P': 0.7,  # top P decode
        'top_K': 20,  # top K decode
    }

    params_refine_text = {
        'prompt': f'[oral_4][laugh_0][break_2]'
    }

    return params_infer_code, params_refine_text


def generate_audio(seed=2):

    """根据 Seed 值，生成音频并保存"""

    params_infer_code, params_refine_text = deterministic(seed)
    print(f"\nThe Seed is {seed}\n")
    text = '曾经有一份真挚的爱情摆在我的面前，但是我没有珍惜，等我失去后才后悔莫及，尘世间最痛苦的事情莫过于此。'
    wavs = chat.infer(text, params_refine_text=params_refine_text,  params_infer_code=params_infer_code)
    torchaudio.save(f"output_{seed}.wav", torch.from_numpy(wavs[0]), 24000)
    print(f"\nThe Seed_{seed} saved.")


if __name__ == "__main__":

    """随机生成 Seed 值，生成多段同文本音频"""

    for i in random.choices(range(100000), k=2):
        generate_audio(i)
