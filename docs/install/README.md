---
sidebar: auto
navbar: True
---

# 部署

你可以使用两种方式部署 TasksManager，这里推荐使用 Docker compose 的方式进行部署。

## Docker Compose 部署

> Docker Compose 是一个用于在使用Compose 文件格式定义的 Docker 上运行多容器应用程序的工具。

### 安装

拉取 TaskManager 程序源码

```shell
git clone https://github.com/raiots/TasksManager.git
```

### 启动
使用 cd 命令进入程序文件夹后启动程序：

```shell
docker-compose up -d
```

TasksManager 将会运行在服务器的 8000 端口，在浏览器中打开 http://ip地址:8000 即可访问

## 使用源码手动部署

> 程序使用 Python3.8 开发，请提前配置 Python 环境

### 安装

使用 git 下载 TasksManager 源码：

```shell
git clone https://github.com/raiots/TasksManager.git
cd TasksManager
```

创建并激活 Python 虚拟环境

```shell
python -m venv venv
.\venv\Scripts\activate.sh
```

安装 TasksManager 依赖

```shell
pip install -r requirements.txt
```

### 启动

```shell
python3 manage.py runserver 0.0.0.0:8000
```

TasksManager 将会运行在服务器的 8000 端口，在浏览器中打开 http://ip地址:8000 即可访问

## 使用 Nginx 配置反向代理

```
server
    {
        listen 443 ssl http2;
        server_name your.domain.com ;


        location / {
            proxy_pass  http://127.0.0.1:8000; # 转发规则
            proxy_set_header Host $proxy_host; # 修改转发请求头，让8000端口的应用可以受到真实的请求
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
```