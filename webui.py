import os
import random
import re
import dotenv

import torch
import gradio as gr
import numpy as np

import ChatTTS

dotenv.load_dotenv()


def generate_seed():

    """生成随机种子"""

    new_seed = random.randint(1, 100000000)
    return {
        "__type__": "update",
        "value": new_seed
        }


def determine_seed(seed):

    """限定模型使用的种子值"""

    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def create_chat(local_path=None):

    """创建ChatTTS实例"""

    local_model_path = os.getenv('MODEL_LOCAL_PATH', None)

    # 导入模型实例
    chat = ChatTTS.Chat()

    if local_model_path is None:
        chat.load_models()
    else:
        print('local model path:', local_model_path)
        chat.load_models('local', local_path=local_model_path)

    return chat


def generate_audio(text, speed, temperature, top_P, top_K, refine_oral, refine_laugh, refine_break, audio_seed_input, text_seed_input, refine_text_flag):

    """生成音频文件"""

    chat = create_chat()

    # 使用音色种子值创建音色
    determine_seed(audio_seed_input)
    rand_spk = chat.sample_random_speaker()

    # 设置文本种子值和文本参数创建口语化风格
    determine_seed(text_seed_input)
    params_infer_code = {
        'spk_emb': rand_spk,
        'prompt': f'[speed_{speed}]',
        'temperature': temperature,
        'top_P': top_P,
        'top_K': top_K,
        }
    params_refine_text = {'prompt': f'[oral_{refine_oral}][laugh_{refine_laugh}][break_{refine_break}]'}

    # 对每个段落分别生成语音
    paragraphs = re.split(r"\n+", text)
    text_data_all = []
    audio_data_all = []
    for paragraph in paragraphs:
        if refine_text_flag:
            paragraph = chat.infer(paragraph,
                                   skip_refine_text=False,
                                   refine_text_only=True,
                                   params_refine_text=params_refine_text,
                                   params_infer_code=params_infer_code
                                   )
        text_data = paragraph[0] if isinstance(paragraph, list) else paragraph
        text_data_all.append(text_data)

        # 生成音频文件
        wav = chat.infer(paragraph,
                         skip_refine_text=True,
                         params_refine_text=params_refine_text,
                         params_infer_code=params_infer_code
                         )
        audio_data = np.array(wav[0]).flatten()
        audio_data_all.append(audio_data)

    # 将所有的语音片段合并成一个完整的音频
    audio_data_all = np.concatenate(audio_data_all)
    sample_rate = 24000

    return [(sample_rate, audio_data_all), '\n\n'.join(text_data_all)]


def playground():

    """创建 Web-UI 交互界面"""

    with gr.Blocks() as demo:
        gr.Markdown("# Awesome-ChatTTS Webui")
        gr.Markdown("Fork from [ChatTTS](https://github.com/2noise/ChatTTS) , 新手指南: [libukai/Awesome-ChatTTS](https://github.com/libukai/Awesome-ChatTTS)")

        default_text = "曾经有一份真挚的爱情摆在我的面前，但是我没有珍惜，等我失去后才后悔莫及，尘世间最痛苦地事情莫过于此。\n\n如果上天能够给我一个再来一次的机会，我会对那个女孩子说三个字：我爱你。 如果非要在这份爱上加上一个期限，我希望是…… 一万年。"
        text_input = gr.Textbox(label="Input Text", lines=4, placeholder="Please Input Text...", value=default_text)

        with gr.Row():
            speed_slider = gr.Slider(minimum=0, maximum=9, step=1, value=2, label="speed")
            temperature_slider = gr.Slider(minimum=0.00001, maximum=1.0, step=0.00001, value=0.3, label="temperature")
            top_p_slider = gr.Slider(minimum=0.1, maximum=0.9, step=0.05, value=0.7, label="top_P")
            top_k_slider = gr.Slider(minimum=1, maximum=20, step=1, value=20, label="top_K")

        with gr.Row():
            refine_text_checkbox = gr.Checkbox(label="Refine text", value=True)
            oral_slider = gr.Slider(minimum=0, maximum=9, step=1, value=3, label="oral")
            laugh_slider = gr.Slider(minimum=0, maximum=9, step=1, value=3, label="laugh")
            break_slider = gr.Slider(minimum=0, maximum=9, step=1, value=3, label="break")

        with gr.Row():
            audio_seed_input = gr.Number(value=2, label="Audio Seed")
            generate_audio_seed = gr.Button("\U0001F3B2")
            text_seed_input = gr.Number(value=42, label="Text Seed")
            generate_text_seed = gr.Button("\U0001F3B2")

        generate_button = gr.Button("Generate")

        text_output = gr.Textbox(label="Output Text", interactive=False)
        audio_output = gr.Audio(label="Output Audio")

        generate_audio_seed.click(generate_seed,
                                  inputs=[],
                                  outputs=audio_seed_input)

        generate_text_seed.click(generate_seed,
                                 inputs=[],
                                 outputs=text_seed_input)

        generate_button.click(generate_audio,
                              inputs=[text_input, speed_slider, temperature_slider, top_p_slider, top_k_slider, oral_slider, laugh_slider, break_slider, audio_seed_input, text_seed_input, refine_text_checkbox],
                              outputs=[audio_output, text_output])

    server_name = os.getenv('SERVER_NAME', '0.0.0.0')
    server_port = int(os.getenv('SERVER_PORT', 8080))
    demo.launch(server_name=server_name, server_port=server_port, inbrowser=True)


if __name__ == '__main__':
    playground()

