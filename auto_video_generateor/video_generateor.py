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
import tempfile
import time

import gradio as gr
import pydub
import requests
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

import tqdm
import qianfan

# import edge_tts

from common_utils import *
from common_utils import _root_dir


def chat(prompt):
    """
    调用千帆免费大语言模型生成文本。
    :param prompt:
    :return:
    """
    chat_comp = qianfan.ChatCompletion()
    # 指定特定模型
    resp = chat_comp.do(model="ERNIE-Speed", messages=[{
        "role": "user",
        "content": prompt
    }])
    # {'id': 'as-dtxjmpmmvi', 'object': 'chat.completion', 'created': 1723638188, 'result': '你好！有什么我可以帮助你的吗？', 'is_truncated': False, 'need_clear_history': False, 'usage': {'prompt_tokens': 1, 'completion_tokens': 8, 'total_tokens': 9}}
    text = resp["body"]["result"]
    return text


# 示例故事文本
def generate_story(prompt, template='{}', code_name="", request: gr.Request = None):
    if request:
        code_name = f'{request.username}/{code_name}'
    get_savepath(code_name, '', mkdir_ok=True)
    story_file = get_savepath(code_name, 'story.txt', mkdir_ok=False)
    if os.path.isfile(story_file):
        return open(story_file, encoding='utf8').read()
    prompt_chat = template.format(prompt)
    story = chat(prompt_chat)
    with open(story_file, 'wt', encoding='utf8') as fout:
        fout.write(story)
    print(f"generate_story 输入: {prompt}")
    print(f"generate_story 输出: {story}")
    return story


# 分句
def split_sentences(story, code_name=""):
    text_dir = get_savepath(code_name, 'text', mkdir_ok=True)

    # sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|。|！|？)\s*', story)
    sentences = re.split(r'([”‘（【《]*.+?[”‘）】》]*[\n。？?！!；;—…：:]+\s*)', story)
    sentences = [w.strip() for sen in sentences for w in re.split(r"(.{10,30}\W+)", sen)
                 if re.search(r'\w', w.strip())]
    for i, sentence in enumerate(tqdm.tqdm(sentences, desc="split_sentences")):
        text_path = f'{text_dir}/text_{i + 100}.txt'
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

from pydub.silence import detect_leading_silence


def synthesize_speech(sentences, voice="zh-CN-YunxiNeural", rate='+0%', volume='+0%', pitch='+0Hz', code_name="",
                      save_path=''):
    if save_path:
        sentences = [sentences]

    audio_dir = get_savepath(code_name, 'audio', mkdir_ok=True)

    voice = voice.split('/')[0]
    rate = "+{}%".format((rate - 50) * 2).replace('+-', '-')
    volume = "+{}%".format((volume - 50) * 2).replace('+-', '-')
    pitch = "+{}Hz".format((pitch - 50)).replace('+-', '-')

    audio_files = []
    for i, sentence in enumerate(tqdm.tqdm(sentences, desc="synthesize_speech")):
        if not sentence:
            continue
        if save_path:
            audio_path = save_path
        else:
            audio_path = f"{audio_dir}/audio_{i + 100}.mp3"
            if os.path.isfile(audio_path):
                audio_files.append(audio_path)
                yield audio_path
                continue
        sentence = re.sub(r'\s+', ' ', sentence)
        # edge-tts --pitch=-50Hz --voice zh-CN-YunyangNeural --text "大家好，欢迎关注我的微信公众号：AI技术实战，我会在这里分享各种AI技术、AI教程、AI开源项目。" --write-media hello_in_cn.mp3
        os.system(
            f'edge-tts --voice {voice} --rate={rate} --volume={volume} --pitch={pitch} --text "{sentence}" --write-media "{audio_path}"')
        # communicate = edge_tts.Communicate(sentence, voice=voice, rate=rate, volume=volume, pitch=pitch)
        # await communicate.save(audio_path)
        seg = pydub.AudioSegment.from_file(audio_path)
        sil_head = detect_leading_silence(seg)
        sil_tail = detect_leading_silence(seg.reverse())
        seg = seg[max(0, sil_head - 150): max(1, len(seg) - sil_tail + 150)]
        seg.export(audio_path, format='mp3')

        audio_files.append(audio_path)
        yield audio_path
    # print(f"synthesize_speech 输入: {sentences}")
    # print(f"synthesize_speech 输出: {audio_files}")
    # return audio_files


def text2image(text, prompt, size="1280x720/抖音B站"):
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
    prompt_image = re.sub(r"\s+", " ", prompt.format(text) if '{}' in prompt else prompt)
    wxh, desc = size.split('/')
    width, height = wxh.split('x')
    seed = ord(desc[-1])
    if prompt_image.startswith('model='):
        g = re.match(r'model=(\w+?)#(.+)$', prompt_image)
        if g:
            model = g.group(1)
            prompt_image = g.group(2)
        else:
            model = 'flux'
    else:
        model = 'flux'  # turbo
    img_url = (f'https://image.pollinations.ai'
               f'/prompt/{prompt_image}'
               f'?width={width}&height={height}&seed={seed}&model={model}&nologo=true')
    try:
        response = requests.get(img_url, verify=False, timeout=(10, 20))
    except Exception as e:
        print(dict(img_url=img_url, error=e))
        import traceback
        traceback.print_exc()
        response = None

    if response and response.status_code == 200:
        img_data = response.content
    else:
        print(dict(response=response, img_url=img_url))
        text = re.sub(r'(\w+?\W+)', r'\1\n', text)
        img_path = add_subtitle(text, image=f'{wxh}/73-109-137', font="msyh.ttc+40", location=(0.5, 0.5),
                                color=(255, 255, 255), image_output='')
        img_data = open(img_path, 'rb').read()
    return img_data


def add_subtitle(text, image="1280x720/73-109-137", font="msyh.ttc+40", location=(0.5, 0.85), color=(255, 255, 255),
                 image_output=''):
    if re.match(r'\d+x\d+/\d+-\d+-\d+', image):
        size, desc = image.split('/')
        width, height = size.split('x')
        red, green, blue = desc.split('-')
        img_path = image

        img = Image.new('RGB', (int(width), int(height)), color=(int(red), int(green), int(blue)))
    else:
        img_path = image
        img = Image.open(img_path)

    d = ImageDraw.Draw(img)

    font_name, font_size = font.split('+')
    # 使用Windows系统中的微软雅黑字体
    font_path = f"C:/Windows/Fonts/{font_name}"  # 微软雅黑字体文件路径
    if not os.path.isfile(font_path):
        font_path = os.path.join(_root_dir, f'static/fonts/{font_name}')
    font_file = ImageFont.truetype(font_path, int(font_size))
    bbox = d.textbbox((0, 0), text, font=font_file)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    width, height = img.size
    x = (width - text_w) * location[0]
    y = (height - text_h) * location[1]
    d.text((x, y), text, font=font_file, fill=color)
    outpath = image_output or (
        img_path if os.path.isfile(img_path) else tempfile.TemporaryFile(prefix='subtitle-', suffix='.png').name)
    img.save(outpath)
    return outpath


def generate_images(sentences, size="1280x720/抖音B站", font="msyh.ttc+40", person="{}", code_name="", save_path=''):
    if save_path:
        sentences = [sentences]

    image_dir = get_savepath(code_name, 'image', mkdir_ok=True)

    # prompt_chat = f'内容：{"".join(sentences)}\n\n请分析以上内容，生成4个词左右的描述图像风格词语，分别从色彩、风格、内容等角度描述，最后仅输出12字以下的文字，输出样例：清新色调，山水画风格，中国寓言故事。'
    # prompt_kw = chat(prompt_chat)
    images = []
    for i, sentence in enumerate(tqdm.tqdm(sentences, desc="generate_images")):
        if not sentence:
            continue
        if save_path:
            img_path = save_path
        else:
            img_path = f"{image_dir}/image_{i + 100}.png"
            if os.path.isfile(img_path):
                images.append(img_path)
                yield img_path
                continue
        # prompt_chat = f'请把以下正文内容翻译为英文，仅输出翻译后的英文内容。正文内容：{sentence}'
        # prompt_chat = f'请把根据内容生成简明扼要的描述内容场景的句子，不能包含人物，输出内容不能包含除场景描述外的其他文字，仅输出场景描述。正文内容：{sentence}'
        # prompt_img = chat(prompt_chat)
        # f'图像风格：{prompt_kw} 图像内容：{sentence} 注意：图中所有人物都用{person}代替，用{person}替换人，去除各种文字，不要任何文字！'

        # prompt_path = f"{image_dir}/image_{i}_prompt.txt"
        # with open(prompt_path, 'wt', encoding='utf8') as fout:
        #     fout.write(prompt_image)

        img_data = text2image(sentence, person, size)

        with open(img_path, 'wb') as fout:
            fout.write(img_data)

        img_path = add_subtitle(sentence, image=img_path, font=font, location=(0.5, 0.85),
                                color=(255, 255, 255), image_output=img_path)

        images.append(img_path)

        yield img_path
    # print(f"generate_images 输入: {sentences}")
    # print(f"generate_images 输出: {images}")
    # return images


def create_resources(texts, prompts, audios, images, code_name):
    """
    ValueError: 'C:\\Users\\kuang\\AppData\\Local\\Temp\\gradio\\610284d670ce6bd048186063a1d5ab89baf955090d8040b446631762a77179ef\\audio_100.wav' is not in the subpath of 'C:\\Users\\kuang\\github\\kuangdd2024\\auto-video-generateor\\mnt\\materials\\abc\\斯坦福监狱实验104' OR one path is relative and the other is absolute.

    :param texts:
    :param prompts:
    :param audios:
    :param images:
    :param code_name:
    :return:
    """
    _save_dir = get_savepath(code_name, '', mkdir_ok=True)

    resource_dir = get_savepath(code_name, 'resource', mkdir_ok=True)

    results = []
    for i, (sen, pmt, aud, img) in enumerate(tqdm.tqdm(zip(texts, prompts, audios, images), desc='create_resources')):
        if not sen:
            continue
        res_path = f"{resource_dir}/resource_{i + 100}.json"

        # dt = dict(index=i, text=sen, prompt=pmt,
        #           audio=get_relpath(code_name, aud),
        #           image=get_relpath(code_name, img),
        #           resource=get_relpath(code_name, res_path))
        dt = dict(index=i, text=sen, prompt=pmt,
                  audio=f'audio/{os.path.basename(aud)}',
                  image=f'image/{os.path.basename(img)}',
                  resource=get_relpath(code_name, res_path))
        with open(res_path, 'wt', encoding='utf8') as fout:
            json.dump(dt, fout, ensure_ascii=False, indent=4)
        yield dt
        results.append([i, sen, pmt, aud, img, res_path])


# 生成视频
def create_video(results, code_name="", save_path='', request: gr.Request = None):
    if request:
        code_name = f'{request.username}/{code_name}'
    _save_dir = get_savepath(code_name, '', mkdir_ok=True)

    if not save_path:
        video_file = get_savepath(code_name, 'video.mp4', mkdir_ok=False)
        if os.path.isfile(video_file):
            return video_file
    else:
        video_file = save_path

    # if not isinstance(results, list):
    #     results = results.to_numpy()
    clips = []
    for dt in tqdm.tqdm(results, desc="create_video"):
        audio = AudioFileClip(get_abspath(code_name, dt["audio"]))
        image = ImageClip(get_abspath(code_name, dt["image"])).set_duration(audio.duration)
        video = image.set_audio(audio)
        clips.append(video)

    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile(video_file, fps=24)
    print(f"create_video 输入: {results}")
    print(f"create_video 输出: {video_file}")
    return video_file


def generate_results(story, size, font, person, voice_input, rate_input, volume_input, pitch_input, code_name=""):
    # global _save_dir
    _save_dir = get_savepath(code_name, '', mkdir_ok=True)
    metadata_file = get_savepath(code_name, 'metadata.json', mkdir_ok=False)

    sents = split_sentences(story, code_name=code_name)

    audios = synthesize_speech(sents, voice_input, rate_input, volume_input, pitch_input, code_name=code_name)
    audios = list(audios)

    images = generate_images(sents, size, font, person, code_name=code_name)
    images = list(images)

    results = create_resources(sents, prompts=[person for _ in sents], audios=audios, images=images,
                               code_name=code_name)
    results = list(results)

    with open(metadata_file, 'wt', encoding='utf8') as fout:
        dt = dict(
            topic='', template='',
            story=story,
            size=size, font=font, person=person,
            voice=voice_input, rate=rate_input, volume=volume_input, pitch=pitch_input,
            code_name=code_name, save_dir=_save_dir, resource_count=len(results)
        )
        json.dump(dt, fout, ensure_ascii=False, indent=4)

    return results


def one_click_pipeline(theme, template, size, font, person, voice_input, rate_input, volume_input, pitch_input,
                       code_name=""):
    get_savepath(code_name, 'text', mkdir_ok=True)

    story = generate_story(theme, template, code_name)
    yield story, None, None
    results = generate_results(story, size, font, person, voice_input, rate_input, volume_input, pitch_input, code_name)
    yield story, results, None
    video = create_video(results, code_name)
    yield story, results, video
