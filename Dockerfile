# 从仓库拉取 带有 python 3.8 的 Linux 环境
FROM python:3.8

# 设置 python 环境变量
ENV PYTHONUNBUFFERED 1

# 创建 code 文件夹并将其设置为工作目录
RUN mkdir /code
WORKDIR /code
# 更新 pip
RUN pip install pip -U
# 将 requirements.txt 复制到容器的 code 目录
ADD requirements.txt /code/
# 安装库
RUN pip install -r requirements.txt -i https://mirrors.ustc.edu.cn/pypi/web/simple
# 将当前目录复制到容器的 code 目录
ADD . /code/
