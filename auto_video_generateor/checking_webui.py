"""
### 资源校对

校对用以合成视频的文本、语音、图像资源，可以修改或重新生成，直到满意。
"""

import argparse, os
import copy
import json
import os
import pathlib
import shutil
import uuid

import librosa
import gradio as gr
import numpy as np
import soundfile

g_json_key_text = ""
g_json_key_prompt = "prompt"
g_json_key_audio = ""
g_json_key_image = ""
g_load_file = ""
g_load_format = ""

g_max_json_index = 0
g_index = 0
g_batch = 10
g_text_list = []
g_prompt_list = []
g_audio_list = []
g_image_list = []
g_resource_list = []
g_checkbox_list = []
g_data_json = []


def reload_data(index, batch):
    global g_index
    g_index = index
    global g_batch
    g_batch = batch
    datas = g_data_json[index:index + batch]
    output = []
    for d in datas:
        output.append(d)
        # output.append(
        #     {
        #         g_json_key_text: d[g_json_key_text],
        #         g_json_key_audio: d[g_json_key_audio],
        #         g_json_key_image: d[g_json_key_image],
        #         g_json_key_prompt: d[g_json_key_prompt]
        #     }
        # )
    return output


def b_change_index(index, batch):
    global g_index, g_batch
    g_index, g_batch = index, batch
    datas = reload_data(index, batch)
    output = []
    # text
    for i, _ in enumerate(datas):
        output.append(
            # gr.Textbox(
            #     label=f"Text {i+index}",
            #     value=_[g_json_key_text]#text
            # )
            {
                "__type__": "update",
                "label": f"【{i + index}】文本",
                "value": _[g_json_key_text]
            }
        )
    for _ in range(g_batch - len(datas)):
        output.append(
            # gr.Textbox(
            #     label=f"Text",
            #     value=""
            # )
            {
                "__type__": "update",
                "label": f"文本",
                "value": ""
            }
        )

    # prompt
    for i, _ in enumerate(datas):
        output.append(
            # gr.Textbox(
            #     label=f"Text {i+index}",
            #     value=_[g_json_key_text]#text
            # )
            {
                "__type__": "update",
                "label": f"图像提示词",
                "value": _[g_json_key_prompt]
            }
        )
    for _ in range(g_batch - len(datas)):
        output.append(
            # gr.Textbox(
            #     label=f"Text",
            #     value=""
            # )
            {
                "__type__": "update",
                "label": f"图像提示词",
                "value": ""
            }
        )

    # audio
    for _ in datas:
        output.append(_[g_json_key_audio])
    for _ in range(g_batch - len(datas)):
        output.append(None)

    # image
    for _ in datas:
        output.append(_[g_json_key_image])
    for _ in range(g_batch - len(datas)):
        output.append(None)

    # resource
    for _ in datas:
        output.append(_)
    for _ in range(g_batch - len(datas)):
        output.append(None)

    # check
    for _ in datas:
        output.append(True)
    for _ in range(g_batch - len(datas)):
        output.append(False)

    return output


def b_next_index(index, batch):
    # b_save_file()
    if (index + batch) <= g_max_json_index:
        return index + batch, *b_change_index(index + batch, batch)
    else:
        return index, *b_change_index(index, batch)


def b_previous_index(index, batch):
    # b_save_file()
    if (index - batch) >= 0:
        return index - batch, *b_change_index(index - batch, batch)
    else:
        return 0, *b_change_index(0, batch)


def b_submit_change(*text_list):
    global g_data_json
    change = False
    for i, new_text in enumerate(text_list):
        if g_index + i <= g_max_json_index:
            new_text = new_text.strip() + ' '
            if (g_data_json[g_index + i][g_json_key_text] != new_text):
                g_data_json[g_index + i][g_json_key_text] = new_text
                change = True
    if change:
        b_save_file()
    return g_index, *b_change_index(g_index, g_batch)


def b_delete_audio(*checkbox_list):
    global g_data_json, g_index, g_max_json_index
    b_save_file()
    change = False
    for i, checkbox in reversed(list(enumerate(checkbox_list))):
        if g_index + i < len(g_data_json):
            if (checkbox == True):
                g_data_json.pop(g_index + i)
                change = True

    g_max_json_index = len(g_data_json) - 1
    if g_index > g_max_json_index:
        g_index = g_max_json_index
        g_index = g_index if g_index >= 0 else 0
    if change:
        b_save_file()
    # return gr.Slider(value=g_index, maximum=(g_max_json_index if g_max_json_index>=0 else 0)), *b_change_index(g_index, g_batch)
    return {"value": g_index, "__type__": "update",
            "maximum": (g_max_json_index if g_max_json_index >= 0 else 0)}, *b_change_index(g_index, g_batch)


def b_invert_selection(*checkbox_list):
    new_list = [not item if item is True else True for item in checkbox_list]
    return new_list


def get_next_path(filename):
    base_dir = os.path.dirname(filename)
    base_name = os.path.splitext(os.path.basename(filename))[0]
    for i in range(100):
        new_path = os.path.join(base_dir, f"{base_name}_{str(i).zfill(2)}.wav")
        if not os.path.exists(new_path):
            return new_path
    return os.path.join(base_dir, f'{str(uuid.uuid4())}.wav')


def b_audio_split(audio_breakpoint, *checkbox_list):
    global g_data_json, g_max_json_index
    checked_index = []
    for i, checkbox in enumerate(checkbox_list):
        if (checkbox == True and g_index + i < len(g_data_json)):
            checked_index.append(g_index + i)
    if len(checked_index) == 1:
        index = checked_index[0]
        audio_json = copy.deepcopy(g_data_json[index])
        path = audio_json[g_json_key_audio]
        data, sample_rate = librosa.load(path, sr=None, mono=True)
        audio_maxframe = len(data)
        break_frame = int(audio_breakpoint * sample_rate)

        if (break_frame >= 1 and break_frame < audio_maxframe):
            audio_first = data[0:break_frame]
            audio_second = data[break_frame:]
            nextpath = get_next_path(path)
            soundfile.write(nextpath, audio_second, sample_rate)
            soundfile.write(path, audio_first, sample_rate)
            g_data_json.insert(index + 1, audio_json)
            g_data_json[index + 1][g_json_key_audio] = nextpath
            b_save_file()

    g_max_json_index = len(g_data_json) - 1
    # return gr.Slider(value=g_index, maximum=g_max_json_index), *b_change_index(g_index, g_batch)
    return {"value": g_index, "maximum": g_max_json_index, "__type__": "update"}, *b_change_index(g_index, g_batch)


def b_merge_audio(interval_r, *checkbox_list):
    global g_data_json, g_max_json_index
    b_save_file()
    checked_index = []
    audios_audio = []
    audios_text = []
    audios_image = []
    for i, checkbox in enumerate(checkbox_list):
        if (checkbox == True and g_index + i < len(g_data_json)):
            checked_index.append(g_index + i)

    if (len(checked_index) > 1):
        for i in checked_index:
            audios_audio.append(g_data_json[i][g_json_key_audio])
            audios_text.append(g_data_json[i][g_json_key_text])
            audios_image.append(g_data_json[i][g_json_key_image])
        for i in reversed(checked_index[1:]):
            g_data_json.pop(i)

        base_index = checked_index[0]
        base_path = audios_audio[0]
        g_data_json[base_index][g_json_key_text] = "".join(audios_text)

        audio_list = []
        l_sample_rate = None
        for i, path in enumerate(audios_audio):
            data, sample_rate = librosa.load(path, sr=l_sample_rate, mono=True)
            l_sample_rate = sample_rate
            if (i > 0):
                silence = np.zeros(int(l_sample_rate * interval_r))
                audio_list.append(silence)

            audio_list.append(data)

        audio_concat = np.concatenate(audio_list)

        soundfile.write(base_path, audio_concat, l_sample_rate)

        b_save_file()

    g_max_json_index = len(g_data_json) - 1

    # return gr.Slider(value=g_index, maximum=g_max_json_index), *b_change_index(g_index, g_batch)
    return {"value": g_index, "maximum": g_max_json_index, "__type__": "update"}, *b_change_index(g_index, g_batch)


def b_save_json():
    with open(g_load_file, 'w', encoding="utf-8") as file:
        for data in g_data_json:
            file.write(f'{json.dumps(data, ensure_ascii=False)}\n')


def b_save_list():
    with open(g_load_file, 'w', encoding="utf-8") as file:
        for data in g_data_json:
            wav_path = data["wav_path"]
            speaker_name = data["speaker_name"]
            language = data["language"]
            text = data["text"]
            file.write(f"{wav_path}|{speaker_name}|{language}|{text}".strip() + '\n')


def b_load_json():
    global g_data_json, g_max_json_index
    with open(g_load_file, 'r', encoding="utf-8") as file:
        g_data_json = file.readlines()
        g_data_json = [json.loads(line) for line in g_data_json]
        g_max_json_index = len(g_data_json) - 1


def b_load_resource():
    global g_data_json, g_max_json_index
    g_data_json = []
    for res_path in sorted(pathlib.Path(g_load_file).glob('*.json')):
        dt = json.load(open(res_path, encoding='utf8'))
        g_data_json.append(dt)
    g_max_json_index = len(g_data_json) - 1


def b_load_list():
    global g_data_json, g_max_json_index
    with open(g_load_file, 'r', encoding="utf-8") as source:
        data_list = source.readlines()
        for _ in data_list:
            data = _.split('|')
            if (len(data) == 4):
                wav_path, speaker_name, language, text = data
                g_data_json.append(
                    {
                        'wav_path': wav_path,
                        'speaker_name': speaker_name,
                        'language': language,
                        'text': text.strip()
                    }
                )
            else:
                print("error line:", data)
        g_max_json_index = len(g_data_json) - 1


def b_save_file():
    if g_load_format == "json":
        b_save_json()
    elif g_load_format == "list":
        b_save_list()


def b_load_file():
    if g_load_format == "json":
        b_load_json()
    elif g_load_format == "list":
        b_load_list()
    elif g_load_format == "resource":
        b_load_resource()


def set_global(load_json, load_list, load_resource, json_key_text, json_key_audio, json_key_image, batch):
    global g_json_key_text, g_json_key_audio, g_json_key_image, g_load_file, g_load_format, g_batch

    g_batch = int(batch)

    if (load_json != "None"):
        g_load_format = "json"
        g_load_file = load_json
    elif (load_list != "None"):
        g_load_format = "list"
        g_load_file = load_list
    else:
        g_load_format = "resource"
        g_load_file = load_resource

    g_json_key_text = json_key_text
    g_json_key_audio = json_key_audio
    g_json_key_image = json_key_image

    b_load_file()


import re


def b_tts(text, audio, tts_check):
    """

    :param text:
    :return:
    """
    if tts_check:
        i = 1
        while os.path.isfile(audio):
            audio = f'{audio}.{i}.mp3'
            i += 1
        sentence = re.sub(r'\s+', ' ', text)
        voice = 'zh-CN-YunxiNeural'
        rate = '+0%'
        volume = '+0%'
        pitch = '+0Hz'
        # edge-tts --pitch=-50Hz --voice zh-CN-YunyangNeural --text "大家好，欢迎关注我的微信公众号：AI技术实战，我会在这里分享各种AI技术、AI教程、AI开源项目。" --write-media hello_in_cn.mp3
        os.system(
            f'edge-tts --voice {voice} --rate={rate} --volume={volume} --pitch={pitch} --text "{sentence}" --write-media "{audio}"')

        res_check = False
        return audio, res_check, tts_check
    else:
        return audio, False, tts_check


import requests


def b_t2i(prompt, text, image, t2i_check):
    """

    :param text:
    :param prompt:
    :return:
    """
    if t2i_check:
        i = 1
        while os.path.isfile(image):
            image = f'{image}.{i}.mp3'
            i += 1
        prompt_image = prompt.format(text) if '{}' in prompt else prompt
        width, height = 1280, 720
        img_url = f'https://image.pollinations.ai/prompt/{prompt_image}?width={width}&height={height}&seed=271828'
        response = requests.get(img_url, verify=False)
        img_data = response.content

        with open(image, 'wb') as fout:
            fout.write(img_data)
        res_check = False
        return image, res_check, t2i_check
    else:
        return image, False, t2i_check


def b_res_check(text, prompt, audio, image, resource, tts_check, t2i_check, res_check):
    """

    :param text:
    :param prompt:
    :param audio:
    :param image:
    :param res_check:
    :return:
    """
    if res_check:
        # if not tts_check:
        #     audio, res_check, tts_check = b_tts(text, audio, True)
        #
        # if not t2i_check:
        #     image, res_check, t2i_check = b_t2i(prompt, text, image, True)
        if audio != resource['audio']:
            shutil.copyfile(audio, resource['audio'])
        audio = resource['audio']

        if image != resource['image']:
            shutil.copyfile(image, resource['image'])
        image = resource['image']

        resource.update(dict(text=text, prompt=prompt))
        res_file = resource['resource']
        with open(res_file, 'wt', encoding='utf8') as fout:
            json.dump(resource, fout, ensure_ascii=False, indent=4)

    return text, prompt, audio, image, resource, tts_check, t2i_check, res_check


def b_text_change(text, resource):
    flag = text == resource['text']
    return flag, flag


def b_prompt_change(prompt, resource):
    flag = prompt == resource['prompt']
    return flag


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--load_json',
                        default=r"None",
                        help='source file, like demo.json')
    parser.add_argument('--is_share', default="False", help='whether webui is_share=True')
    parser.add_argument('--load_list', default="None", help='source file, like demo.list')
    parser.add_argument('--load_resource',
                        default=r"/directory/to/resource",
                        help='source file, like /resource')
    parser.add_argument('--webui_port_subfix', default=9871, help='source file, like demo.list')
    parser.add_argument('--json_key_text', default="text", help='the text key name in json, Default: text')
    parser.add_argument('--json_key_audio', default="audio", help='the path key name in json, Default: audio')
    parser.add_argument('--json_key_image', default="image", help='the path key name in json, Default: image')
    parser.add_argument('--g_batch', default=10, help='max number g_batch wav to display, Default: 10')

    args = parser.parse_args()

    set_global(args.load_json, args.load_list, args.load_resource, args.json_key_text, args.json_key_audio,
               args.json_key_image,
               args.g_batch)

    with gr.Blocks() as demo:

        with gr.Row():
            btn_change_index = gr.Button("跳转")
            btn_submit_change = gr.Button("生成视频")
            btn_merge_audio = gr.Button("合并资源")
            btn_delete_audio = gr.Button("删除资源")
            btn_previous_index = gr.Button("上一页")
            btn_next_index = gr.Button("下一页")

        with gr.Row():
            index_slider = gr.Slider(
                minimum=0, maximum=g_max_json_index, value=g_index, step=1, label="序号", scale=3
            )
            splitpoint_slider = gr.Slider(
                minimum=0, maximum=120.0, value=0, step=0.1, label="切分点", scale=3
            )
            btn_audio_split = gr.Button("切分资源", scale=1)
            btn_save_json = gr.Button("保存资源", visible=True, scale=1)
            btn_invert_selection = gr.Button("反转选择", scale=1)
        video_output = gr.Video(
            label="视频",
            visible=True,
            scale=5
        )
        with gr.Row():
            with gr.Column():
                for _ in range(0, g_batch):
                    with gr.Row():
                        with gr.Column():
                            with gr.Column():
                                with gr.Row():
                                    text = gr.Textbox(
                                        label="文本",
                                        visible=True,
                                        scale=5
                                    )
                                    tts_check = gr.Checkbox(
                                        label="已生成",
                                        value=True,
                                        show_label=True,
                                        info="生成语音",
                                        scale=1
                                    )

                                with gr.Row():
                                    prompt = gr.Textbox(
                                        label="图像提示词",
                                        visible=True,
                                        scale=5
                                    )
                                    t2i_check = gr.Checkbox(
                                        label="已生成",
                                        value=True,
                                        show_label=True,
                                        info="生成图像",
                                        scale=1
                                    )

                            with gr.Row():
                                resource = gr.Json(
                                    label="资源",
                                    value={},
                                    visible=True,
                                    scale=5
                                )
                                res_check = gr.Checkbox(
                                    label="已确认",
                                    value=True,
                                    show_label=True,
                                    info="确认使用当前文本、语音和图像",
                                    scale=1
                                )
                        with gr.Column():
                            audio = gr.Audio(
                                label="语音",
                                type='filepath',
                                visible=True,
                                # scale=1
                            )
                            image = gr.Image(
                                label="图像",
                                type='filepath',
                                visible=True,
                                # scale=5
                            )

                        text.change(b_text_change, inputs=[text, resource], outputs=[tts_check, t2i_check])
                        prompt.change(b_prompt_change, inputs=[prompt, resource], outputs=[t2i_check])
                        tts_check.change(b_tts, inputs=[text, audio, tts_check], outputs=[audio, res_check, tts_check])
                        t2i_check.change(b_t2i, inputs=[prompt, text, image, t2i_check],
                                         outputs=[image, res_check, t2i_check])
                        res_check.change(b_res_check,
                                         inputs=[text, prompt, audio, image, resource, tts_check, t2i_check, res_check],
                                         outputs=[text, prompt, audio, image, resource, tts_check, t2i_check,
                                                  res_check])

                        g_text_list.append(text)
                        g_prompt_list.append(prompt)
                        g_audio_list.append(audio)
                        g_image_list.append(image)
                        g_resource_list.append(resource)
                        g_checkbox_list.append(res_check)

        with gr.Row():
            batchsize_slider = gr.Slider(
                minimum=1, maximum=g_batch, value=g_batch, step=1, label="单页数量", scale=3, interactive=False
            )
            interval_slider = gr.Slider(
                minimum=0, maximum=2, value=0, step=0.01, label="间隔数量", scale=3
            )
            btn_theme_dark = gr.Button("Light Theme", link="?__theme=light", scale=1)
            btn_theme_light = gr.Button("Dark Theme", link="?__theme=dark", scale=1)

        total_list = [
            *g_text_list,
            *g_prompt_list,
            *g_audio_list,
            *g_image_list,
            *g_resource_list,
            *g_checkbox_list,
        ]

        btn_change_index.click(
            b_change_index,
            inputs=[
                index_slider,
                batchsize_slider,
            ],
            outputs=total_list,
        )

        btn_submit_change.click(
            b_submit_change,
            inputs=[
                *g_text_list,
            ],
            outputs=[
                index_slider,
                *total_list
            ],
        )

        btn_previous_index.click(
            b_previous_index,
            inputs=[
                index_slider,
                batchsize_slider,
            ],
            outputs=[
                index_slider,
                *total_list
            ],
        )

        btn_next_index.click(
            b_next_index,
            inputs=[
                index_slider,
                batchsize_slider,
            ],
            outputs=[
                index_slider,
                *total_list
            ],
        )

        btn_delete_audio.click(
            b_delete_audio,
            inputs=[
                *g_checkbox_list
            ],
            outputs=[
                index_slider,
                *total_list
            ]
        )

        btn_merge_audio.click(
            b_merge_audio,
            inputs=[
                interval_slider,
                *g_checkbox_list
            ],
            outputs=[
                index_slider,
                *total_list
            ]
        )

        btn_audio_split.click(
            b_audio_split,
            inputs=[
                splitpoint_slider,
                *g_checkbox_list
            ],
            outputs=[
                index_slider,
                *total_list
            ]
        )

        btn_invert_selection.click(
            b_invert_selection,
            inputs=[
                *g_checkbox_list
            ],
            outputs=[
                *g_checkbox_list
            ]
        )

        btn_save_json.click(
            b_save_file
        )

        demo.load(
            b_change_index,
            inputs=[
                index_slider,
                batchsize_slider,
            ],
            outputs=total_list,
        )

    demo.launch(
        server_name="0.0.0.0",
        inbrowser=True,
        quiet=True,
        share=eval(args.is_share),
        server_port=int(args.webui_port_subfix)
    )
