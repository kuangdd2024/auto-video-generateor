"""
## 基于千帆大模型的自动视频生成
基于百度的千帆大模型生成故事和图像，然后进一步生成视频。

### 相关文档
[API列表 - 千帆大模型平台 | 百度智能云文档 (baidu.com)](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Nlks5zkzu)
[Python SDK快速入门 - 千帆大模型平台 | 百度智能云文档 (baidu.com)](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/3lmokh7n6)
[Stable-Diffusion-XL - 千帆大模型平台 | 百度智能云文档 (baidu.com)](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Klkqubb9w)
[ERNIE-4.0-8K - 千帆大模型平台 | 百度智能云文档 (baidu.com)](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/clntwmv7t)
"""
import os
import re
import time

import gradio as gr
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import tqdm

import qianfan

os.environ["QIANFAN_ACCESS_KEY"] = "ALTAKc5yYaLe5QS***********"
os.environ["QIANFAN_SECRET_KEY"] = "eb058f32d47a4c5*****************"

t_now = time.strftime('%Y-%m-%d_%H.%M.%S')

# 保存材料的目录请自行设定，暂用时间戳区分不同项目
_root_dir = os.path.dirname(os.path.dirname(__file__))
_save_dir = os.path.join(_root_dir, f'mnt/materials/{t_now}')

os.makedirs(_save_dir, exist_ok=True)

import pyttsx3

tts_engine = pyttsx3.init()


# 示例故事文本
def generate_story(prompt, story_file=f'{_save_dir}/story.txt'):
    # story = "从前有一个农夫，每天辛勤地在田里耕作。一天，他在田里看到一只兔子撞到树桩上死了。农夫非常高兴，把兔子带回家美餐了一顿。从那以后，他每天都守在树桩旁，希望再捡到撞死的兔子。结果，他再也没有捡到兔子，田里的庄稼也荒废了。" if theme == "守株待兔" else f"这是一个关于{theme}的故事。"
    chat_comp = qianfan.ChatCompletion()
    prompt = f"请根据正文内容生成故事，要求内容丰富，文字限制在200字以内。正文内容：{prompt}"
    # 指定特定模型
    resp = chat_comp.do(model="ERNIE-Speed", messages=[{
        "role": "user",
        "content": prompt
    }])
    # {'id': 'as-dtxjmpmmvi', 'object': 'chat.completion', 'created': 1723638188, 'result': '你好！有什么我可以帮助你的吗？', 'is_truncated': False, 'need_clear_history': False, 'usage': {'prompt_tokens': 1, 'completion_tokens': 8, 'total_tokens': 9}}
    story = resp["body"]["result"]

    with open(story_file, 'wt', encoding='utf8') as fout:
        fout.write(story)
    print(f"generate_story 输入: {prompt}")
    print(f"generate_story 输出: {story}")
    return story


# 分句
def split_sentences(story, text_dir=f'{_save_dir}/text'):
    os.makedirs(text_dir, exist_ok=True)

    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|。|！|？)\s*', story)
    sentences = [w.strip() for w in sentences if w.strip()]
    for i, sentence in enumerate(tqdm.tqdm(sentences, desc="split_sentences")):
        text_path = f'{text_dir}/text_{i}.txt'
        with open(text_path, 'wt', encoding='utf8') as fout:
            fout.write(sentence)
    print(f"split_sentences 输入: {story}")
    print(f"split_sentences 输出: {sentences}")
    return sentences


def text_to_speech(text, filename):
    engine = pyttsx3.init()
    # 设置语音属性（可选）
    engine.setProperty('rate', 150)  # 语速
    engine.setProperty('volume', 1)  # 音量

    # 保存语音到文件
    engine.save_to_file(text, filename)
    engine.runAndWait()


# 语音合成占位
def synthesize_speech(sentences, audio_dir=f'{_save_dir}/audio'):
    os.makedirs(audio_dir, exist_ok=True)

    audio_files = []
    for i, sentence in enumerate(tqdm.tqdm(sentences, desc="synthesize_speech")):
        audio_path = f"{audio_dir}/audio_{i}.wav"
        tts_engine.save_to_file(text=sentence, filename=audio_path)
        tts_engine.runAndWait()
        audio_files.append(audio_path)
    print(f"synthesize_speech 输入: {sentences}")
    print(f"synthesize_speech 输出: {audio_files}")
    return audio_files


def text2image(prompt):
    """
    生成图片长宽，说明：
（1）默认值 1024x1024，
（2）取值范围如下：
· 适用头像： ["768x768", "1024x1024", "1536x1536", "2048x2048"]
· 适用文章配图 ：["1024x768", "2048x1536"]
· 适用海报传单：["768x1024", "1536x2048"]
· 适用电脑壁纸：["1024x576", "2048x1152"]
· 适用海报传单：["576x1024", "1152x2048"]

    生成风格。说明：
（1）默认值为Base
（2）可选值：
· Base：基础风格
· 3D Model：3D模型
· Analog Film：模拟胶片
· Anime：动漫
· Cinematic：电影
· Comic Book：漫画
· Craft Clay：工艺黏土
· Digital Art：数字艺术
· Enhance：增强
· Fantasy Art：幻想艺术
· Isometric：等距风格
· Line Art：线条艺术
· Lowpoly：低多边形
· Neonpunk：霓虹朋克
· Origami：折纸
· Photographic：摄影
· Pixel Art：像素艺术
· Texture：纹理
    :param prompt:
    :return:
    """
    t2i = qianfan.Text2Image()
    # 文心一格（微调后）
    # resp = t2i.do(prompt="A Ragdoll cat with a bowtie.", with_decode="base64",endpoint="your_custom_endpoint")
    prompt = f"请首先根据正文内容生成细节丰富的图像，人物请用中国人。正文内容：{prompt}"
    resp = t2i.do(prompt=prompt, with_decode="base64", model="Stable-Diffusion-XL",
                  size="1024x576", n=1, retry_count=3, style="Cinematic")
    img_data = resp["body"]["data"][0]["image"]
    return img_data


# 文字图片占位
def generate_images(sentences, image_dir=f'{_save_dir}/image'):
    os.makedirs(image_dir, exist_ok=True)

    images = []
    for i, sentence in enumerate(tqdm.tqdm(sentences, desc="generate_images")):
        img_data = text2image(sentence)
        img_path = f"{image_dir}/image_{i}.png"
        with open(img_path, 'wb') as fout:
            fout.write(img_data)
        images.append(img_path)
    print(f"generate_images 输入: {sentences}")
    print(f"generate_images 输出: {images}")
    return images


# 生成视频
def create_video(sentences, audio_files, images, video_file=f'{_save_dir}/video.mp4'):
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


# Gradio 交互界面
def process_story(theme):
    story = generate_story(theme)
    return story


def generste_results(story):
    sents = split_sentences(story)
    ids = [w + 1 for w in range(len(sents))]
    audios = synthesize_speech(sents)
    images = generate_images(sents)
    results = list(zip(ids, sents, audios, images))
    return results


def generate_sentences(story):
    return [[w, 'audio', 'image'] for w in split_sentences(story)]


def synthesize_audios_for_sentences(sentences):
    return [[w] for w in synthesize_speech([w[0] for w in sentences])]


def generate_images_for_sentences(sentences):
    return [w for w in generate_images([w[0] for w in sentences])]


def create_final_video(results):
    print(results)
    sentences, audio_files, images = [], [], []
    for i, text, audio, image in results.to_numpy():
        sentences.append(text)
        audio_files.append(audio)
        images.append(image)
    return create_video(sentences, audio_files, images)


with gr.Blocks() as demo:
    theme_input = gr.Textbox(label="主题文字", placeholder="输入一个主题文字", value="守株待兔")

    with gr.Row():
        theme_button = gr.Button("生成故事")
        result_button = gr.Button("生成资源")
        create_video_button = gr.Button("生成视频")
    story_output = gr.Textbox(label="故事文本")

    results_output = gr.Dataframe(headers=["序号", "文本", "语音", "图像"],
                                  label="视频所需资源")
    video_output = gr.Video(label="视频")

    theme_button.click(
        fn=process_story,
        inputs=theme_input,
        outputs=[story_output],
    )
    result_button.click(
        fn=generste_results,
        inputs=story_output,
        outputs=results_output,
    )
    create_video_button.click(
        fn=create_final_video,
        inputs=results_output,
        outputs=video_output,
    )

if __name__ == "__main__":
    demo.launch(server_name='127.0.0.1', server_port=8000, show_error=True)
