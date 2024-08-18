"""
## 免费的自动视频生成

全部用免费的资源实现，体现完整流程和初步效果。

### 相关文档
[千帆ModelBuilder 部分ERNIE系列模型免费开放公告 - 千帆大模型平台 | 百度智能云文档 (baidu.com)](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/wlwg8f1i3)
[ERNIE-Speed-128K - 千帆大模型平台 | 百度智能云文档 (baidu.com)](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/6ltgkzya5)
[如何用GPT直接生成AI绘画？ - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/639471405)
[2.8k star! 用开源免费的edge-tts平替科大讯飞的语音合成服务 - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/685186002)
"""
import hashlib
import json
import os
import pathlib
import re
import time

import gradio as gr
import requests
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

import tqdm
import qianfan

# import edge_tts

# 自行在环境变量设置千帆的参数
# os.environ["QIANFAN_ACCESS_KEY"] = "ALTAKc5yYaLe5QS***********"
# os.environ["QIANFAN_SECRET_KEY"] = "eb058f32d47a4c5*****************"

t_now = time.strftime('%Y-%m-%d_%H.%M.%S')

# 保存材料的目录请自行设定，暂用时间戳区分不同项目
_root_dir = os.path.dirname(os.path.dirname(__file__))
_save_dir = os.path.join(_root_dir, f'mnt/materials/{t_now}')

os.makedirs(_save_dir, exist_ok=True)


def chat(prompt):
    """
    调用千帆免费大语言模型生成文本。
    :param prompt:
    :return:
    """
    chat_comp = qianfan.ChatCompletion()
    # 指定特定模型
    resp = chat_comp.do(model="ERNIE-Speed-128k", messages=[{
        "role": "user",
        "content": prompt
    }])
    # {'id': 'as-dtxjmpmmvi', 'object': 'chat.completion', 'created': 1723638188, 'result': '你好！有什么我可以帮助你的吗？', 'is_truncated': False, 'need_clear_history': False, 'usage': {'prompt_tokens': 1, 'completion_tokens': 8, 'total_tokens': 9}}
    text = resp["body"]["result"]
    return text


# 示例故事文本
def generate_story(prompt, template='{}', story_file=""):
    story_file = story_file or f'{_save_dir}/story.txt'
    prompt_chat = template.format(prompt)
    story = chat(prompt_chat)
    with open(story_file, 'wt', encoding='utf8') as fout:
        fout.write(story)
    print(f"generate_story 输入: {prompt}")
    print(f"generate_story 输出: {story}")
    return story


# 分句
def split_sentences(story, text_dir=""):
    text_dir = text_dir or f'{_save_dir}/text'
    os.makedirs(text_dir, exist_ok=True)

    # sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|。|！|？)\s*', story)
    sentences = re.split(r'([”‘（【《]*.+?[”‘）】》]*[\n。？?！!；;—…：:]+\s*)', story)
    sentences = [w.strip() for sen in sentences for w in re.split(r"(.{10,30}\W+)", sen)
                 if re.search(r'\w', w.strip())]
    for i, sentence in enumerate(tqdm.tqdm(sentences, desc="split_sentences")):
        text_path = f'{text_dir}/text_{i}.txt'
        with open(text_path, 'wt', encoding='utf8') as fout:
            fout.write(sentence)
    print(f"split_sentences 输入: {story}")
    print(f"split_sentences 输出: {sentences}")
    return sentences


def get_tts_voices():
    """
Name: zh-CN-XiaoxiaoNeural
Gender: Female

Name: zh-CN-XiaoyiNeural
Gender: Female

Name: zh-CN-YunjianNeural
Gender: Male

Name: zh-CN-YunxiNeural
Gender: Male

Name: zh-CN-YunxiaNeural
Gender: Male

Name: zh-CN-YunyangNeural
Gender: Male

Name: zh-CN-liaoning-XiaobeiNeural
Gender: Female

Name: zh-CN-shaanxi-XiaoniNeural
Gender: Female

Name: zh-HK-HiuGaaiNeural
Gender: Female

Name: zh-HK-HiuMaanNeural
Gender: Female

Name: zh-HK-WanLungNeural
Gender: Male

Name: zh-TW-HsiaoChenNeural
Gender: Female

Name: zh-TW-HsiaoYuNeural
Gender: Female

Name: zh-TW-YunJheNeural
Gender: Male

    :return:
    """
    voices = ['zh-CN-XiaoxiaoNeural/Female', 'zh-CN-XiaoyiNeural/Female', 'zh-CN-YunjianNeural/Male',
              'zh-CN-YunxiNeural/Male',
              'zh-CN-YunxiaNeural/Male', 'zh-CN-YunyangNeural/Male', 'zh-CN-liaoning-XiaobeiNeural/Female',
              'zh-CN-shaanxi-XiaoniNeural/Female', 'zh-HK-HiuGaaiNeural/Female', 'zh-HK-HiuMaanNeural/Female',
              'zh-HK-WanLungNeural/Male', 'zh-TW-HsiaoChenNeural/Female', 'zh-TW-HsiaoYuNeural/Female',
              'zh-TW-YunJheNeural/Male']
    return voices


zh_voices = get_tts_voices()


def synthesize_speech(sentences, voice="zh-CN-YunxiNeural", rate='+0%', volume='+0%', pitch='+0Hz', audio_dir=""):
    voice = voice.split('/')[0]
    rate = "+{}%".format((rate - 50) * 2).replace('+-', '-')
    volume = "+{}%".format((volume - 50) * 2).replace('+-', '-')
    pitch = "+{}Hz".format((pitch - 50)).replace('+-', '-')
    audio_dir = audio_dir or f'{_save_dir}/audio'
    os.makedirs(audio_dir, exist_ok=True)

    audio_files = []
    for i, sentence in enumerate(tqdm.tqdm(sentences, desc="synthesize_speech")):
        audio_path = f"{audio_dir}/audio_{i}.mp3"
        sentence = re.sub(r'\s+', ' ', sentence)
        # edge-tts --pitch=-50Hz --voice zh-CN-YunyangNeural --text "大家好，欢迎关注我的微信公众号：AI技术实战，我会在这里分享各种AI技术、AI教程、AI开源项目。" --write-media hello_in_cn.mp3
        os.system(
            f'edge-tts --voice {voice} --rate={rate} --volume={volume} --pitch={pitch} --text "{sentence}" --write-media "{audio_path}"')
        # communicate = edge_tts.Communicate(sentence, voice=voice, rate=rate, volume=volume, pitch=pitch)
        # await communicate.save(audio_path)

        audio_files.append(audio_path)
    print(f"synthesize_speech 输入: {sentences}")
    print(f"synthesize_speech 输出: {audio_files}")
    return audio_files


def text2image(prompt, size="1280x720"):
    """
    `![Image](https://image.pollinations.ai/prompt/{prompt}?width=<Number>&height=<Number>)`

你应该将prompt替换为上面的文字，并配上合适的宽高尺寸。请注意尺寸最多不超过1024px。同时，你需要将URL Encode处理，最终的结果就像下面这样：

![Image](https://image.pollinations.ai/prompt/A%20beautiful%2022-year-old%20Chinese%20woman%20with%20long%20black%20hair,%20big%20eyes,%20and%20a%20pair%20of%20dimples,%20smiling%20at%20the%20camera?width=768&height=512)

在使用Pollinations.ai进行图像生成时，输入控制字段通常涉及以下几个步骤：

访问Pollinations.ai平台：首先，您需要打开浏览器并访问Pollinations.ai的官方网站。

选择模型：如果平台提供了多个AI模型，选择一个适合您需求的模型来进行图像生成。

输入描述：在提供的文本框中输入描述性文本，这将作为AI生成图像的主要依据。描述应尽可能详细，包括场景、颜色、风格、主题等元素。

设置参数：如果需要，您可以设置图像的宽度、高度、随机种子等参数。这些参数可以帮助您控制图像的尺寸和确保生成的一致性。

选择风格和流派：根据需要，选择图像的视觉风格（如现实主义、卡通等）和流派（如科幻、奇幻等）。

艺术家参考：如果需要，您可以指定一个艺术家或风格作为参考，以便AI生成的图像具有特定的艺术风格。

提交生成请求：完成所有设置后，点击生成按钮提交您的请求。

查看和保存结果：AI将根据您提供的描述和参数生成图像。生成完成后，您可以查看图像，并根据需要进行保存或进一步编辑。

以下是一个示例，展示如何构建一个请求：

https://image.pollinations.ai/prompt/%5Bdescription%5D?width=1920&height=1080&seed=12345&style=realistic&genre=scifi&artist=Vincent_van_Gogh
在这个例子中：

%5Bdescription%5D 是URL编码后的描述字段，实际使用时应替换为具体的描述文本。
width 和 height 分别设置了图像的宽度和高度。
seed 是随机种子，用于生成图像的一致性。
style 指定了图像的风格，这里是“realistic”（现实主义）。
genre 指定了图像的流派，这里是“scifi”（科幻）。
artist 指定了参考的艺术家，这里是“Vincent_van_Gogh”（文森特·梵高）。
    :param prompt:
    :return:
    """
    size, desc = size.split('/')
    width, height = size.split('x')
    seed = ord(desc[-1])
    img_url = f'https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}&seed={seed}'
    response = requests.get(img_url, verify=False)
    img_data = response.content
    return img_data


def generate_images(sentences, size="1280x720", font="msyh.ttc+40", person="{}", image_dir=""):
    image_dir = image_dir or f'{_save_dir}/image'
    os.makedirs(image_dir, exist_ok=True)
    # prompt_chat = f'内容：{"".join(sentences)}\n\n请分析以上内容，生成4个词左右的描述图像风格词语，分别从色彩、风格、内容等角度描述，最后仅输出12字以下的文字，输出样例：清新色调，山水画风格，中国寓言故事。'
    # prompt_kw = chat(prompt_chat)
    images = []
    for i, sentence in enumerate(tqdm.tqdm(sentences, desc="generate_images")):
        # prompt_chat = f'请把以下正文内容翻译为英文，仅输出翻译后的英文内容。正文内容：{sentence}'
        # prompt_chat = f'请把根据内容生成简明扼要的描述内容场景的句子，不能包含人物，输出内容不能包含除场景描述外的其他文字，仅输出场景描述。正文内容：{sentence}'
        # prompt_img = chat(prompt_chat)
        # f'图像风格：{prompt_kw} 图像内容：{sentence} 注意：图中所有人物都用{person}代替，用{person}替换人，去除各种文字，不要任何文字！'
        prompt_image = re.sub(r"\s+", " ", person.format(sentence))
        img_path = f"{image_dir}/image_{i}_prompt.txt"
        with open(img_path, 'wt', encoding='utf8') as fout:
            fout.write(prompt_image)

        img_data = text2image(prompt_image, size)
        img_path = f"{image_dir}/image_{i}.png"
        with open(img_path, 'wb') as fout:
            fout.write(img_data)

        # (1280, 720)
        # img = Image.new('RGB', (720, 480), color=(73, 109, 137))
        img = Image.open(img_path)
        d = ImageDraw.Draw(img)

        font_name, font_size = font.split('+')
        # 使用Windows系统中的微软雅黑字体
        font_path = f"C:/Windows/Fonts/{font_name}"  # 微软雅黑字体文件路径
        if not os.path.isfile(font_path):
            font_path = os.path.join(_root_dir, f'static/fonts/{font_name}')
        font_file = ImageFont.truetype(font_path, int(font_size))
        text = sentence.strip()
        bbox = d.textbbox((0, 0), text, font=font_file)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        width, height = img.size
        x = (width - text_w) / 2
        y = (height - text_h) * 0.85
        d.text((x, y), text, font=font_file, fill=(255, 255, 255))
        img_path = f"{image_dir}/image_{i}.png"
        img.save(img_path)
        images.append(img_path)
    print(f"generate_images 输入: {sentences}")
    print(f"generate_images 输出: {images}")
    return images


# 生成视频
def create_video(sentences, audio_files, images, video_file=""):
    video_file = video_file or f'{_save_dir}/video.mp4'
    clips = []
    for i, (sentence, audio_path, img_path) in enumerate(
            tqdm.tqdm(zip(sentences, audio_files, images), desc="create_video")):
        audio = AudioFileClip(audio_path)
        image = ImageClip(img_path).set_duration(audio.duration)
        video = image.set_audio(audio)
        clips.append(video)

    final_video = concatenate_videoclips(clips, method="compose")
    final_video_path = f"{video_file}"
    final_video.write_videofile(final_video_path, fps=24)
    print(f"create_video 输入: {sentences}, {audio_files}, {images}")
    print(f"create_video 输出: {final_video_path}")
    return final_video_path


def process_story(topic, template):
    global _save_dir
    t_now = time.strftime('%Y-%m-%d_%H.%M.%S')

    # 保存材料的目录请自行设定，暂用时间戳区分不同项目
    _save_dir = os.path.join(_root_dir, f'mnt/materials/{t_now}')
    os.makedirs(_save_dir, exist_ok=True)

    story = generate_story(topic, template)
    return story


def generate_results(story, size, font, person, voice_input, rate_input, volume_input, pitch_input, resource_dir=""):
    resource_dir = resource_dir or f'{_save_dir}/resource'
    os.makedirs(resource_dir, exist_ok=True)

    resource_file = f'{resource_dir}.json'
    sents = split_sentences(story)
    ids = [w for w in range(len(sents))]
    audios = synthesize_speech(sents, voice_input, rate_input, volume_input, pitch_input)
    images = generate_images(sents, size, font, person)
    results = list(zip(ids, sents, audios, images))

    with open(resource_file, 'wt', encoding='utf8') as fout:
        dt = dict(story=story,
                  size=size, font=font, person=person,
                  voice=voice_input, rate=rate_input, volume=volume_input, pitch=pitch_input,
                  datetime=t_now, resource=_save_dir, count=len(results))
        json.dump(dt, fout, ensure_ascii=False, indent=4)

    for idx, sen, aud, img in results:
        res_path = f"{resource_dir}/resource_{idx}.json"
        dt = dict(index=idx, text=sen, prompt=person, audio=aud, image=img, resource=res_path)
        with open(res_path, 'wt', encoding='utf8') as fout:
            json.dump(dt, fout, ensure_ascii=False, indent=4)

    return results


def generate_sentences(story):
    return [[w, 'audio', 'image'] for w in split_sentences(story)]


def synthesize_audios_for_sentences(sentences):
    return [[w] for w in synthesize_speech([w[0] for w in sentences])]


def generate_images_for_sentences(sentences):
    return [w for w in generate_images([w[0] for w in sentences])]


def create_final_video(results):
    print(results)
    if not isinstance(results, list):
        results = results.to_numpy()
    sentences, audio_files, images = [], [], []
    for i, text, audio, image in results:
        sentences.append(text)
        audio_files.append(audio)
        images.append(image)
    return create_video(sentences, audio_files, images)


def one_click_pipeline(topic, template, size, font, person, voice_input, rate_input, volume_input, pitch_input):
    global _save_dir
    t_now = time.strftime('%Y-%m-%d_%H.%M.%S')

    # 保存材料的目录请自行设定，暂用时间戳区分不同项目
    _save_dir = os.path.join(_root_dir, f'mnt/materials/{t_now}')
    os.makedirs(_save_dir, exist_ok=True)

    story = process_story(topic, template)
    yield story, None, None
    results = generate_results(story, size, font, person, voice_input, rate_input, volume_input, pitch_input)
    yield story, results, None
    video = create_final_video(results)
    yield story, results, video


with gr.Blocks() as demo:
    gr.Markdown("## 自动视频生成器")
    gr.Markdown("### 故事参数设置")
    with gr.Row():
        topic_input = gr.Textbox(label="主题", placeholder="输入主题内容", value="守株待兔")
        template_input = gr.Textbox(label="提示词模板", placeholder="输入提示词模板，用{}表示放主题文字的地方",
                                    value="内容：```{}```\n\n请根据以上代码块的内容生成故事，要求内容丰富，限制在200字以内。")

    gr.Markdown("### 图像参数设置")
    image_sizes = ["768x768/头像", "1024x1024/头像", "1536x1536/头像", "2048x2048/头像",  # · 适用头像：
                   "1024x768/文章配图", "2048x1536/文章配图",  # · 适用文章配图 ：
                   "768x1024/海报传单", "1536x2048/海报传单",  # · 适用海报传单：
                   "1024x576/电脑壁纸", "2048x1152/电脑壁纸",  # · 适用电脑壁纸：
                   "576x1024/海报传单", "1152x2048/海报传单",  # · 适用海报传单：
                   "426x240/240p",  # 像素（240p）
                   "320:240/流畅240p4:3"  # 流畅
                   "640x360/流畅360p",  # 像素（360p）
                   "854x480/标清480p",  # 像素（480p）
                   "640x480/标清480p4:3"  # 标清
                   "720x480/标清480p3:2"  # 标清
                   "1280x720/高清720p抖音B站",  # 像素（720p）油管，西瓜视频，B站，抖音
                   "1920x1080/全高清1080p",  # 像素（1080p）
                   "2560x1440/2K",  # 像素（1440p）
                   "2048x1080/2K1:1.9",  # 2K视频
                   "3840x2160/4K",  # 像素（2160p）
                   "7680x4320/8K",  # 全超高清
                   "1920x1080/竖版抖音",  # 竖版视频到抖音
                   ]
    font_choices = [f'{w.name}+{s}' for w in sorted(pathlib.Path(pathlib.Path(_root_dir).joinpath("static", "fonts")).glob('*')) for s in [24, 32, 40]]
    with gr.Row():
        person_input = gr.Textbox(label="风格描述", placeholder="输入风格、限制等描述，用{}表示放正文内容",
                                  value="图像内容：{} 图像限制：图中所有人物都用大熊猫代替，必须用大熊猫替换人，去除各种文字，不要任何文字！")
        size_input = gr.Dropdown(image_sizes, value="1280x720/抖音B站", label="图像大小", allow_custom_value=True)
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

    results_output = gr.Dataframe(headers=["序号", "文本", "语音", "图像"],
                                  label="视频所需资源")
    video_output = gr.Video(label="视频")
    one_button.click(
        fn=one_click_pipeline,
        inputs=[topic_input, template_input, size_input, font_input, person_input, voice_input, rate_input,
                volume_input, pitch_input],
        outputs=[story_output, results_output, video_output],
    )

    topic_button.click(
        fn=process_story,
        inputs=[topic_input, template_input],
        outputs=[story_output],
    )
    result_button.click(
        fn=generate_results,
        inputs=[story_output, size_input, font_input, person_input, voice_input, rate_input, volume_input, pitch_input],
        outputs=results_output,
    )
    create_video_button.click(
        fn=create_final_video,
        inputs=results_output,
        outputs=video_output,
    )

if __name__ == "__main__":
    demo.launch(server_name='127.0.0.1', server_port=8000, show_error=True)
