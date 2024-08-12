import os
import re
import time

import gradio as gr
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

t_now = time.strftime('%Y-%m-%d_%H.%M.%S')

# 保存材料的目录请自行设定，暂用时间戳区分不同项目
_save_dir = f'mnt/materials/{t_now}'

os.makedirs(_save_dir, exist_ok=True)

import pyttsx3

tts_engine = pyttsx3.init()


# 示例故事文本
def generate_story(theme, story_file=f'{_save_dir}/story.txt'):
    story = "从前有一个农夫，每天辛勤地在田里耕作。一天，他在田里看到一只兔子撞到树桩上死了。农夫非常高兴，把兔子带回家美餐了一顿。从那以后，他每天都守在树桩旁，希望再捡到撞死的兔子。结果，他再也没有捡到兔子，田里的庄稼也荒废了。" if theme == "守株待兔" else f"这是一个关于{theme}的故事。"
    with open(story_file, 'wt', encoding='utf8') as fout:
        fout.write(story)
    print(f"generate_story 输入: {theme}")
    print(f"generate_story 输出: {story}")
    return story


# 分句
def split_sentences(story, text_dir=f'{_save_dir}/text'):
    os.makedirs(text_dir, exist_ok=True)

    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|。|！|？)\s*', story)
    sentences = [w.strip() for w in sentences if w.strip()]
    for i, sentence in enumerate(sentences):
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


# def text_to_speech(text):
#     engine = pyttsx3.init()
#     engine.say(text)
#     engine.runAndWait()
#
# text = "这是一个示例文本，用于演示文本转语音。"
# text_to_speech(text)


# 语音合成占位
def synthesize_speech(sentences, audio_dir=f'{_save_dir}/audio'):
    os.makedirs(audio_dir, exist_ok=True)

    audio_files = []
    for i, sentence in enumerate(sentences):
        audio_path = f"{audio_dir}/audio_{i}.wav"
        tts_engine.save_to_file(text=sentence, filename=audio_path)
        tts_engine.runAndWait()
        audio_files.append(audio_path)
    print(f"synthesize_speech 输入: {sentences}")
    print(f"synthesize_speech 输出: {audio_files}")
    return audio_files


# 文字图片占位
def generate_images(sentences, image_dir=f'{_save_dir}/image'):
    os.makedirs(image_dir, exist_ok=True)

    images = []
    for i, sentence in enumerate(sentences):
        # (1280, 720)
        img = Image.new('RGB', (720, 480), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        # 使用Windows系统中的微软雅黑字体
        font_path = "C:/Windows/Fonts/msyh.ttc"  # 微软雅黑字体文件路径
        font = ImageFont.truetype(font_path, 24)
        text = sentence
        bbox = d.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        width, height = img.size
        x = (width - text_w) / 2
        y = (height - text_h) / 2
        d.text((x, y), text, font=font, fill=(255, 255, 255))
        img_path = f"{image_dir}/image_{i}.png"
        img.save(img_path)
        images.append(img_path)
    print(f"generate_images 输入: {sentences}")
    print(f"generate_images 输出: {images}")
    return images


# 生成视频
def create_video(sentences, audio_files, images, video_file=f'{_save_dir}/video.mp4'):
    clips = []
    for i, (sentence, audio_path, img_path) in enumerate(zip(sentences, audio_files, images)):
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

demo.launch(server_name='127.0.0.1', server_port=8000, show_error=True)
