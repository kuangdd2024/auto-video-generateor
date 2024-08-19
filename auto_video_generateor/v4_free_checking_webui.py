"""
## 视频生成并校对

自动生成视频及其文本、语音、图像素材，支持人工校对素材并修改，然后生成新的视频。
"""
import gradio

from common_utils import *
from video_generateor import *
from resource_checking import *

from common_utils import _root_dir


# 自行在环境变量设置千帆的参数
# os.environ["QIANFAN_ACCESS_KEY"] = "ALTAKc5yYaLe5QS***********"
# os.environ["QIANFAN_SECRET_KEY"] = "eb058f32d47a4c5*****************"


def b_video_output_change(code_name, video_output):
    """

    :param story_output:
    :param results_output:
    :param video_output:
    :return:
    """
    if code_name:
        res_path = get_savepath(code_name, 'resource', mkdir_ok=False)
    else:
        res_path = os.path.join(os.path.dirname(video_output), 'resource')
    g_data_json = b_load_resource(res_path)
    data_list = b_change_index(0, g_batch, g_data_json=g_data_json)
    video_check = video_output
    return video_check, *data_list


def b_load_click(code_name):
    """加载资源"""

    res_path = get_savepath(code_name, 'resource', mkdir_ok=False)

    story_path = get_savepath(code_name, 'story.txt', mkdir_ok=False)
    story_check = open(story_path, encoding='utf8').read()

    g_data_json = b_load_resource(res_path)
    data_list = b_change_index(0, g_batch, g_data_json=g_data_json)

    video_check = get_savepath(code_name, 'video.mp4', mkdir_ok=False)

    return story_check, video_check, *data_list


def b_generate_click(topic, template, size, font, person, voice_input, rate_input, volume_input, pitch_input,
                     code_name=""):
    """
    total_list = [
    *g_text_list,
    *g_prompt_list,
    *g_audio_list,
    *g_image_list,
    *g_resource_list,
    *g_checkbox_list,
]
    :param story:
    :param size:
    :param font:
    :param person:
    :param voice_input:
    :param rate_input:
    :param volume_input:
    :param pitch_input:
    :param code_name:
    :return:
    """
    _save_dir = get_savepath(code_name, '', mkdir_ok=True)

    metadata_file = get_savepath(code_name, 'metadata.json', mkdir_ok=False)

    story = ''
    video = None
    g_text_list = ['' for _ in range(g_max_json_index)]
    g_prompt_list = ['' for _ in range(g_max_json_index)]
    g_audio_list = [None for _ in range(g_max_json_index)]
    g_image_list = [None for _ in range(g_max_json_index)]
    g_resource_list = [{} for _ in range(g_max_json_index)]
    g_checkbox_list = [False for _ in range(g_max_json_index)]

    total_list = [
        *g_text_list,
        *g_prompt_list,
        *g_audio_list,
        *g_image_list,
        *g_resource_list,
        *g_checkbox_list,
    ]

    story = generate_story(topic, template, code_name)
    yield story, video, *total_list

    sents = split_sentences(story, code_name=code_name)
    for idx, text in enumerate(sents):
        total_list[idx] = text
        yield story, video, *total_list

    for idx, text in enumerate(sents):
        total_list[g_max_json_index + idx] = person
        yield story, video, *total_list

    audios = synthesize_speech(sents, voice_input, rate_input, volume_input, pitch_input, code_name=code_name)
    for idx, audio in enumerate(audios):
        total_list[2 * g_max_json_index + idx] = audio
        yield story, video, *total_list

    images = generate_images(sents, size, font, person, code_name=code_name)
    for idx, image in enumerate(images):
        total_list[3 * g_max_json_index + idx] = image
        yield story, video, *total_list

    n_sents = len(sents)
    resources = create_resources(texts=total_list[: n_sents],
                                 prompts=total_list[g_max_json_index: g_max_json_index + n_sents],
                                 audios=total_list[2 * g_max_json_index: 2 * g_max_json_index + n_sents],
                                 images=total_list[3 * g_max_json_index: 3 * g_max_json_index + n_sents],
                                 code_name=code_name)
    resources = list(resources)

    for idx, res in enumerate(resources):
        total_list[4 * g_max_json_index + idx] = res
        yield story, video, *total_list

    for idx, _ in enumerate(sents):
        total_list[5 * g_max_json_index + idx] = True
        yield story, video, *total_list

    with open(metadata_file, 'wt', encoding='utf8') as fout:
        dt = dict(topic=topic, template=template, story=story,
                  size=size, font=font, person=person,
                  voice=voice_input, rate=rate_input, volume=volume_input, pitch=pitch_input,
                  code_name=code_name, save_dir=_save_dir, resource_count=n_sents)
        json.dump(dt, fout, ensure_ascii=False, indent=4)

    video = create_video(resources, code_name)
    yield story, video, *total_list


def b_compose_video(code_name, *resource_list):
    video_file = get_savepath(code_name, 'video.mp4', mkdir_ok=False)
    if os.path.isfile(video_file):
        t = time.strftime(r'%Y%m%d%H%M%S')
        video_file = re.sub(r'([a-zA-Z]+)(\.?\d*)\.(\w+?)$', rf'\1.{t}.\3', video_file)
    else:
        video_file = tempfile.TemporaryFile(prefix='video-', suffix='.mp4').name

    total_list = resource_list
    results = []
    for idx, (sen, pmt, aud, img, res, check) in enumerate(zip(total_list[:g_max_json_index],
                                                               total_list[g_max_json_index: 2 * g_max_json_index],
                                                               total_list[2 * g_max_json_index: 3 * g_max_json_index],
                                                               total_list[3 * g_max_json_index: 4 * g_max_json_index],
                                                               total_list[4 * g_max_json_index: 5 * g_max_json_index],
                                                               total_list[5 * g_max_json_index: 6 * g_max_json_index])):
        if not check:
            continue
        results.append(dict(index=idx, text=sen, prompt=pmt, audio=aud, image=img, resource=res))

    video = create_video(results=results, code_name=code_name, save_path=video_file)
    return video, False


def b_tts_change(text, audio, tts_check, voice="zh-CN-YunxiNeural", rate='+0%', volume='+0%', pitch='+0Hz',
                 code_name=""):
    """

    :param text:
    :return:
    """
    if tts_check:
        if audio:
            if os.path.isfile(audio):
                t = time.strftime(r'%Y%m%d%H%M%S')
                audio = re.sub(r'_(\d+)(\.?\d*)\.(\w+?)$', rf'_\1.{t}.\3', audio)
        else:
            audio = tempfile.TemporaryFile(prefix='tts-', suffix='.mp3').name

        audio = synthesize_speech(text, voice, rate, volume, pitch, code_name=code_name, save_path=audio)
        audio = next(audio)

        res_check = False
        return audio, res_check, tts_check
    else:
        return audio, False, tts_check


def b_t2i_change(text, image, t2i_check, size="1280x720/抖音B站", font="msyh.ttc+40", person="{}", code_name=""):
    """

    :param text:
    :param prompt:
    :return:
    """
    if t2i_check:
        if image:
            if os.path.isfile(image):
                t = time.strftime(r'%Y%m%d%H%M%S')
                image = re.sub(r'_(\d+)(\.?\d*)\.(\w+?)$', rf'_\1.{t}.\3', image)
        else:
            image = tempfile.TemporaryFile(prefix='t2i-', suffix='.png').name

        image = generate_images(text, size, font, person, code_name=code_name, save_path=image)
        image = next(image)

        res_check = False
        return image, res_check, t2i_check
    else:
        return image, False, t2i_check


def b_confirm_check_change(code_name, video, confirm_check):
    video_file = get_savepath(code_name, 'video.mp4', mkdir_ok=False)
    if confirm_check:
        if video_check != video_file:
            shutil.copyfile(video, video_file)
    else:
        video_file = video
    return video_file


def b_res_check(text, prompt, audio, image, resource, tts_check, t2i_check, res_check, code_name):
    """

    :param text:
    :param prompt:
    :param audio:
    :param image:
    :param res_check:
    :return:
    """
    if res_check and resource:
        res_audio = get_abspath(code_name, resource['audio'])
        if audio != res_audio:
            shutil.copyfile(audio, res_audio)
        audio = res_audio

        res_image = get_abspath(code_name, resource['image'])
        if image != res_image:
            shutil.copyfile(image, res_image)
        image = res_image

        resource.update(dict(text=text, prompt=prompt))
        res_file = get_abspath(code_name, resource['resource'])
        with open(res_file, 'wt', encoding='utf8') as fout:
            json.dump(resource, fout, ensure_ascii=False, indent=4)

    return text, prompt, audio, image, resource, tts_check, t2i_check, res_check


def b_load_param_click(code_name):
    """
        load_param_btn.click(b_load_param_click,
                         inputs=[code_name_input],
                         outputs=[topic_input, template_input, size_input, font_input, person_input, voice_input,
                                  rate_input, volume_input, pitch_input])
{
    "story": "习得性无助的逆袭：小明的“破茧成蝶”之路\n\n话说，曾经的小明是梦想的航船，怀揣万千憧憬驶向远方。可那狠心的老爸，老是扯破帆、打破舵，总对他说：“你啊，不是那一块金子”。这种无形的挫败感让小明的理想之旅充满了阴霾。就像一个故事里的燕子，迷失了自我，觉得自己遇到了习得性无助。直到有一天……历经无数挫折的小明，终于明白：人生不止眼前的苟且，还有诗和远方。他想起那句古话：“山重水复疑无路，柳暗花明又一村”。重整旗鼓，咬牙坚持。这不，后来的故事大家都知道了，小明真的飞上了天空——他的梦想成真了！逆风翻盘的英雄总是让人热血沸腾！习得性无助并不可怕，只要心中有火，终会破茧成蝶！",
    "size": "1280x720/抖音B站",
    "font": "msyh.ttc+32",
    "person": "图像内容：{} 图像限制：图中所有人物都用大熊猫代替，必须用大熊猫替换人，去除各种文字，不要任何文字！",
    "voice": "zh-CN-YunxiNeural/Male",
    "rate": 50,
    "volume": 50,
    "pitch": 50,
    "code_name": "2024-08-18_12.34.52",
    "save_dir": "C:/Users/kuang/github/kuangdd2024/auto-video-generateor/mnt/materials/习得性无助（屡次碰壁后放弃）/",
    "resource_count": 17
}
    :return:
    """
    meta_path = get_savepath(code_name, 'metadata.json', mkdir_ok=False)
    metadata = json.load(open(meta_path, encoding='utf8'))
    keys = ['topic', 'template', 'story', 'size', 'font', 'person', 'voice', 'rate', 'volume', 'pitch']
    defaults = ['', '', '', '', '', '', '', 0, 0, 0]
    outputs = []
    for key, value in zip(keys, defaults):
        outputs.append(metadata.get(key, value))
    return outputs[0], *outputs[1:]


g_text_list = []
g_prompt_list = []
g_audio_list = []
g_image_list = []
g_resource_list = []
g_checkbox_list = []
g_data_json = []

code_name_choices = [w.name for w in sorted(pathlib.Path(get_savepath('', '', mkdir_ok=False)).glob('*'))]

template_value = """内容：```{}```

请根据以上代码块的内容生成口语风格的文案；前面部分讲解内容核心，用比喻、排比等修辞，引用古诗词、谚语等名句；后半部分讲案例故事，用抖音电影解说风格，语言风趣幽默；整个文案限制在300字以内。"""

image_prompt_value = "图像内容：{} 图像限制：电影风格，写实主义，唯美画风，环境简单"

with gr.Blocks() as demo:
    gr.Markdown("## 自动视频生成器")
    with gr.Row():
        code_name_input = gr.Dropdown(code_name_choices, value="请输入代号名称", label="代号名称（支持自定义输入）",
                                      allow_custom_value=True)
        # force_check = gr.Checkbox(
        #     label="强制更新",
        #     value=True,
        #     show_label=True,
        #     info="在生成资源过程中，是否强制更新资源",
        #     scale=1
        # )
        generate_button = gr.Button("生成资源")
        with gr.Column():
            load_param_btn = gr.Button("加载参数")
            load_button = gr.Button("加载资源")

    with gr.Tabs():
        with gr.TabItem("参数设置"):
            gr.Markdown("### 故事参数设置")
            with gr.Row():
                topic_input = gr.Textbox(label="主题", placeholder="输入主题内容", value="")
                template_input = gr.Textbox(label="提示词模板", placeholder="输入提示词模板，用{}表示放主题文字的地方",
                                            value=template_value)

            gr.Markdown("### 图像参数设置")
            image_sizes = [
                "768x768/头像", "1024x1024/头像", "1536x1536/头像", "2048x2048/头像",  # · 适用头像：
                "1024x768/文章配图", "2048x1536/文章配图",  # · 适用文章配图 ：
                "768x1024/海报传单", "1536x2048/海报传单",  # · 适用海报传单：
                "1024x576/电脑壁纸", "2048x1152/电脑壁纸",  # · 适用电脑壁纸：
                "576x1024/海报传单", "1152x2048/海报传单",  # · 适用海报传单：
                "426x240/240p",  # 像素（240p）
                "320x240/流畅240p4:3",  # 流畅
                "640x360/流畅360p",  # 像素（360p）
                "640x480/标清480p4:3",  # 标清
                "854x480/标清480p",  # 像素（480p）
                "720x480/标清480p3:2",  # 标清
                "1280x720/高清720p抖音B站",  # 像素（720p）油管，西瓜视频，B站，抖音
                "1920x1080/全高清1080p",  # 像素（1080p）
                "2048x1080/2K1:1.9",  # 2K视频
                "2560x1440/2K",  # 像素（1440p）
                "3840x2160/4K",  # 像素（2160p）
                "7680x4320/8K",  # 全超高清
                "1080x1920/竖版抖音",  # 竖版视频到抖音
                "720x1280/竖版720p",  # 像素（720p）油管，西瓜视频，B站，抖音
                "360x640/竖版360p",  # 像素（360p）
                "480x640/竖版480p4:3",  # 标清
                "480x720/竖版480p3:2",  # 标清
            ]
            font_choices = [f'{w.name}+{s}' for w in
                            sorted(pathlib.Path(pathlib.Path(_root_dir).joinpath("static", "fonts")).glob('*')) for s in
                            [24, 32, 40]]
            with gr.Row():
                person_input = gr.Textbox(label="风格描述", placeholder="输入风格、限制等描述，用{}表示放正文内容",
                                          value=image_prompt_value)
                size_input = gr.Dropdown(image_sizes, value="1280x720/抖音B站", label="图像大小",
                                         allow_custom_value=True)
                # size_input = gr.Textbox(label="图像大小", placeholder="输入图像的宽度x高度，例如：1280x720", value="1280x720")
                font_input = gr.Dropdown(font_choices, value="msyh.ttc+32", label="字体参数", allow_custom_value=True)
                # font_input = gr.Textbox(label="字体参数", placeholder="输入字体类型+大小字号：", value="msyh.ttc+32")

            gr.Markdown('### 语音参数设置')
            with gr.Row():
                voice_input = gr.Dropdown(zh_voices, value=zh_voices[3], label="发音人", allow_custom_value=True)
                rate_input = gr.Slider(minimum=0, maximum=100, value=50, step=1, label="语速")
                volume_input = gr.Slider(minimum=0, maximum=100, value=50, step=1, label="音量")
                pitch_input = gr.Slider(minimum=0, maximum=100, value=50, step=1, label="音调")

            one_button = gr.Button("一键生成")

            with gr.Row():
                topic_button = gr.Button("生成故事")
                result_button = gr.Button("生成资源")
                create_video_button = gr.Button("生成视频")
            story_output = gr.Textbox(label="故事文本")

            results_output = gr.Dataframe(headers=["序号", "文本", "生图词", "语音", "图像", "资源"],
                                          label="视频所需资源")
            video_output = gr.Video(label="视频")
            one_button.click(
                fn=one_click_pipeline,
                inputs=[topic_input, template_input, size_input, font_input, person_input, voice_input, rate_input,
                        volume_input, pitch_input, code_name_input],
                outputs=[story_output, results_output, video_output],
            )

            topic_button.click(
                fn=generate_story,
                inputs=[topic_input, template_input, code_name_input],
                outputs=[story_output],
            )
            result_button.click(
                fn=generate_results,
                inputs=[story_output, size_input, font_input, person_input, voice_input, rate_input, volume_input,
                        pitch_input],
                outputs=results_output,
            )
            create_video_button.click(
                fn=create_video,
                inputs=results_output,
                outputs=video_output,
            )
        with gr.TabItem("资源校对"):
            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        btn_submit_change = gr.Button("生成视频")
                        confirm_check = gr.Checkbox(
                            label="已确认",
                            value=True,
                            show_label=True,
                            info="确认使用该视频"
                        )
                    btn_invert_selection = gr.Button("反转选择")
                with gr.Column():
                    btn_merge_audio = gr.Button("合并资源")
                    with gr.Row():
                        btn_audio_split = gr.Button("切分资源")
                        splitpoint_slider = gr.Slider(
                            minimum=0, maximum=120.0, value=0, step=0.1, label="切分点"
                        )
                with gr.Column():
                    btn_save_json = gr.Button("增加资源")
                    btn_delete_audio = gr.Button("删除资源")

            story_check = gr.Textbox(label="故事", lines=5)
            video_check = gr.Video(
                label="视频",
                visible=True,
                scale=5
            )
            with gr.Row():
                with gr.Column():
                    for idx in range(0, g_batch):
                        idx_slider = gr.Slider(
                            minimum=1, maximum=g_max_json_index, value=idx + 1, step=1,
                            label="资源序号", interactive=False
                        )
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

                            # text.change(b_text_change, inputs=[text, resource], outputs=[tts_check, t2i_check])
                            # prompt.change(b_prompt_change, inputs=[prompt, resource], outputs=[t2i_check])
                            tts_check.change(b_tts_change, inputs=[text, audio, tts_check,
                                                                   voice_input, rate_input, volume_input, pitch_input,
                                                                   code_name_input],
                                             outputs=[audio, res_check, tts_check])
                            t2i_check.change(b_t2i_change,
                                             inputs=[text, image, t2i_check,
                                                     size_input, font_input, prompt, code_name_input],
                                             outputs=[image, res_check, t2i_check])
                            res_check.change(b_res_check,
                                             inputs=[text, prompt, audio, image, resource, tts_check, t2i_check,
                                                     res_check, code_name_input],
                                             outputs=[text, prompt, audio, image, resource, tts_check, t2i_check,
                                                      res_check])

                            g_text_list.append(text)
                            g_prompt_list.append(prompt)
                            g_audio_list.append(audio)
                            g_image_list.append(image)
                            g_resource_list.append(resource)
                            g_checkbox_list.append(res_check)
            with gr.Row():
                with gr.Column():
                    btn_change_index = gr.Button("跳转")
                    index_slider = gr.Slider(
                        minimum=0, maximum=g_max_json_index, value=0, step=1, label="序号"
                    )  # value=g_index
                btn_previous_index = gr.Button("上一页")
                btn_next_index = gr.Button("下一页")
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

            # btn_submit_change.click(
            #     b_submit_change,
            #     inputs=[
            #         *g_text_list,
            #     ],
            #     outputs=[
            #         index_slider,
            #         *total_list
            #     ],
            # )

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

            # demo.load(
            #     b_change_index,
            #     inputs=[
            #         index_slider,
            #         batchsize_slider,
            #     ],
            #     outputs=total_list,
            # )
    video_output.change(b_video_output_change,
                        inputs=[code_name_input, video_output],
                        outputs=[video_check, *total_list])
    load_param_btn.click(b_load_param_click,
                         inputs=[code_name_input],
                         outputs=[topic_input, template_input, story_output,
                                  size_input, font_input, person_input, voice_input,
                                  rate_input, volume_input, pitch_input])
    load_button.click(b_load_click,
                      inputs=[code_name_input],
                      outputs=[story_check, video_check, *total_list])
    generate_button.click(b_generate_click,
                          inputs=[topic_input, template_input, size_input, font_input, person_input, voice_input,
                                  rate_input,
                                  volume_input, pitch_input, code_name_input],
                          outputs=[story_check, video_check, *total_list])
    btn_submit_change.click(b_compose_video, inputs=[code_name_input, *total_list],
                            outputs=[video_check, confirm_check])
    confirm_check.change(b_confirm_check_change, inputs=[code_name_input, video_check, confirm_check],
                         outputs=[video_check])

if __name__ == "__main__":
    demo.queue(max_size=1022).launch(
        server_name="127.0.0.1",  # "0.0.0.0",
        inbrowser=True,
        share=True,  # True,
        server_port=8000,
        quiet=True,
        # auth=lambda x, y: x == y,  # ("admin", "pass1234"),
        # auth_message='欢迎来到自动视频生成的世界'
    )
