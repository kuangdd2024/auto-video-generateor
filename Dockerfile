FROM python:3.10-slim-bullseye

LABEL maintainer="kuangdd@qq.com"
ARG TZ='Asia/Shanghai'

ARG CHATGPT_ON_WECHAT_VER

RUN echo /etc/apt/sources.list
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list
ENV BUILD_PREFIX=/app

RUN mkdir -p ${BUILD_PREFIX}

RUN apt-get update \
    && apt-get install -y --no-install-recommends --fix-missing bash vim ffmpeg wget zip

COPY ./requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt -i https://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com
#RUN pip install --no-cache-dir -r /tmp/requirements.txt -i http://mirrors.cloud.tencent.com/pypi/simple --trusted-host mirrors.cloud.tencent.com

WORKDIR ${BUILD_PREFIX}

COPY . ${BUILD_PREFIX}

CMD python main.py
