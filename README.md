# auto-video-generateor

自动视频生成器，给定主题，自动生成解说视频。用户输入主题文字，系统调用大语言模型生成故事或解说的文字，然后进一步调用语音合成接口生成解说的语音，调用文生图接口生成契合文字内容的配图，最后融合语音和配图生成解说视频。

## 🌈️⭐️

❤️️🌈喜欢的话，不妨“点石成金”点 Star ⭐️，你的点⭐️是我的动力，感谢🎉🌟！

## 视频样例先睹为快

<table class="center">
  <tr style="font-weight: bolder;text-align:center;">
        <td width="50%">免费并校对：人的本性是天生的吗</td>
        <td width="50%">免费并校对：归去来兮辞</td>
  </tr>
  <tr>
    <td >
      <video src=https://github.com/user-attachments/assets/1d0b8e67-1809-451b-9eef-53e21b25b626 controls preload></video>
    </td>
    <td >
      <video src=https://github.com/user-attachments/assets/fc83780c-03b0-4323-a8af-286040b5e4dd controls preload></video>
    </td>
  </tr>
  <tr style="font-weight: bolder;text-align:center;">
        <td width="50%">免费并校对：空白效应</td>
        <td width="50%">免费并校对：棘轮效应</td>
  </tr>
  <tr>
    <td >
      <video src=https://github.com/user-attachments/assets/cbfdd5dd-2ad0-43bf-ae36-47bd18d13a21 controls preload></video>
    </td>
    <td >
      <video src=https://github.com/user-attachments/assets/b1e3ff8f-9049-4aba-adc7-707e4b16d27b controls preload></video>
    </td>
  </tr>
</table>

## 体验Demo

- 体验地址：http://avg.kddbot.com/

- 扫码关注“趣聊机器人”微信公众号，体验该项目的效果：

  ![kddbot_qrcode.png](static/kddbot_qrcode.png)

- 在”趣聊机器人“对话框输入”自动视频生成账密获取“（无引号），获取账号密码。

- 可能生成视频资源速度比较慢，请耐心等待，或者在一段时间后，通过“加载参数”和“加载资源”来加载已经生成好的视频资源。

- 如果图片是文字图片，则可能后台生成图片有异常，用文字图片替代，这种情况则稍后再试试。

- 一定要整个流程跑一遍之后才能修改单个素材资源，跑一遍指的是“一键生成”执行完毕，或各个分步骤逐个执行一遍，特别是“创建记录”这步要执行。

## v4. 免费+校对生成

先自动批量合成视频所需素材，然后校对用以合成视频的文本、语音、图像资源，可以修改或重新生成，直到满意。

![free_checking.jpg](static/free_checking.png)

### 使用简要指引

- 生成资源和视频，从零开始，自动生成视频

![avg_generating.png](static/avg_generating.png)

- 加载参数和资源，快捷加载已有数据，进一步生成视频

![avg_loading.png](static/avg_loading.png)

- 校对资源和生成，校对文本、语音、图像资源，生成满意视频

![avg_checking.png](static/avg_checking.png)

## 免费的自动视频生成

全部用免费的资源实现，体现完整流程和初步效果。

### 相关文档

[千帆ModelBuilder 部分ERNIE系列模型免费开放公告 - 千帆大模型平台 | 百度智能云文档 (baidu.com)](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/wlwg8f1i3)

[ERNIE-Speed-128K - 千帆大模型平台 | 百度智能云文档 (baidu.com)](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/6ltgkzya5)

[如何用GPT直接生成AI绘画？ - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/639471405)

[2.8k star! 用开源免费的edge-tts平替科大讯飞的语音合成服务 - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/685186002)

## 基于千帆的自动视频生成

基于百度的千帆大模型生成故事和图像，然后进一步生成视频。

### 相关文档

[API列表 - 千帆大模型平台 | 百度智能云文档 (baidu.com)](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Nlks5zkzu)

[Python SDK快速入门 - 千帆大模型平台 | 百度智能云文档 (baidu.com)](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/3lmokh7n6)

[Stable-Diffusion-XL - 千帆大模型平台 | 百度智能云文档 (baidu.com)](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Klkqubb9w)

[ERNIE-4.0-8K - 千帆大模型平台 | 百度智能云文档 (baidu.com)](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/clntwmv7t)

## 极简的自动视频生成

实现这个系统需要多个步骤，包括生成故事文本、分句、语音合成、文生图、生成视频、以及使用Gradio进行交互。

- 步骤 1: 生成故事文本
  为了简化，我们先手动创建一个示例故事文本。

- 步骤 2: 分句
  使用`re`库或自然语言处理工具将文本分句。

- 步骤 3: 语音合成
  使用`pyttsx3`库或其他语音合成模型进行语音合成。

- 步骤 4: 文生图
  使用`pillow`库或其他文生图模型生成图片。

- 步骤 5: 生成视频
  使用`moviepy`库将图片和音频组合成视频。

- 步骤 6: 使用Gradio实现交互
  使用`gradio`库创建一个简单的交互界面。

## 资源校对交互页面

校对用以合成视频的文本、语音、图像资源，可以修改或重新生成，直到满意。

## 使用方法

### 执行代码

```shell
# 参数可选：1 2 3 4
python main.py 4
```

### 打开浏览器

http://127.0.0.1:8000/

### 交互操作

用户在gradio界面输入主题文字，生成并编辑故事文本，然后生成语音、图片资源，最终合成视频。

### 注意事项

1. 生成视频后会把生成的文本、语音、图片的多媒体材料保存到目录中（默认：mnt/materials/username/code_name）。

2. 保存多媒体材料的目录结构样例如下：

```text
code_name
│  metadata.json
│  story.txt
│  video.mp4
│
├─audio
│      audio_100.mp3
│      audio_101.mp3
│      audio_102.mp3
│      audio_103.mp3
│      audio_104.mp3
│      audio_105.mp3
│      audio_106.mp3
│      audio_107.mp3
│
├─image
│      image_100.png
│      image_101.png
│      image_102.png
│      image_103.png
│      image_104.png
│      image_105.png
│      image_106.png
│      image_107.png
│
├─resource
│      resource_100.json
│      resource_101.json
│      resource_102.json
│      resource_103.json
│      resource_104.json
│      resource_105.json
│      resource_106.json
│      resource_107.json
│
└─text
        text_100.txt
        text_101.txt
        text_102.txt
        text_103.txt
        text_104.txt
        text_105.txt
        text_106.txt
        text_107.txt
```

## todo list

- [x] 设置参数时候语音支持试听
- [x] 设置参数时候文生图提示词支持生成样例图
- [x] 字体支持预览效果
- [ ] 资源校对完善切分、合并、增加、删除的操作
- [x] 支持输入故事开始生成视频
- [x] 去除图片里的水印（等比例截取画面、调用去水印接口）
- [ ] 写代码注释
- [ ] 录制操作视频
- [ ] 支持批量下载文本、语音、图片等素材资源
- [ ] 字幕和图片分离，字幕在制作视频时候再添加
