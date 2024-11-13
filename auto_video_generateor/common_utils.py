import os
import time
import pathlib

import gradio
import qianfan

# 自行在环境变量设置千帆的参数
# os.environ["QIANFAN_ACCESS_KEY"] = "ALTAKc5yYaLe5QS***********"
# os.environ["QIANFAN_SECRET_KEY"] = "eb058f32d47a4c5*****************"

t_now = time.strftime('%Y-%m-%d_%H.%M.%S')

# 保存材料的目录请自行设定，暂用时间戳区分不同项目
_root_dir = os.path.dirname(os.path.dirname(__file__))
_save_dir = os.path.join(_root_dir, f'mnt/materials/{t_now}')


def get_savepath(code_name, sub_name, mkdir_ok=True, request: gradio.Request = None):
    if request:
        code_name = f'{request.username}/{code_name}'  # or time.strftime('%Y-%m-%d_%H.%M.%S')

    # 保存材料的目录请自行设定，暂用时间戳区分不同项目
    _save_dir = os.path.join(_root_dir, f'mnt/materials/{code_name}')

    savepath = f'{_save_dir}/{sub_name}'.replace('\\', '/')
    savepath.rstrip('/')
    if mkdir_ok:
        os.makedirs(savepath, exist_ok=True)
    # print(dict(savepath=savepath))
    return savepath


def get_relpath(code_name, abspath, request: gradio.Request = None):
    _save_dir = get_savepath(code_name, '', mkdir_ok=False, request=request)
    relpath = '/'.join(pathlib.Path(abspath).relative_to(_save_dir).parts)
    return relpath


def get_abspath(code_name, relpath, request: gradio.Request = None):
    _save_dir = get_savepath(code_name, '', mkdir_ok=False, request=request)
    abspath = '/'.join(pathlib.Path(_save_dir).joinpath(relpath).parts)
    return abspath


# os.makedirs(_save_dir, exist_ok=True)
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
