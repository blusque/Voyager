# Voyager 在阿里云/腾讯云的部署与运行指南（中文）

本指南适用于将 Voyager 及其依赖（Minecraft Java 服务器、Mineflayer Node 服务、Python 主控）部署在阿里云 ECS 或腾讯云 CVM 上进行长期运行与训练/探索。

> 说明：本项目仍需使用 Minecraft 官方登录（Microsoft 账号 OAuth），即使计算资源在阿里/腾讯云。你需要在首次运行时完成一次浏览器登录并把重定向后的 URL 粘贴回终端。

---

## 1. 架构与端口

- 组件构成：
  - Minecraft Java 服务器（Fabric Loader 1.19 + Mods，项目会自动拉起）
  - Mineflayer 桥接服务（Node.js，默认监听 3000）
  - Voyager Python 主控（调度 LLM、与 Mineflayer 通信）
- 典型端口：
  - 25565/tcp：Minecraft 服务器端口（如需从外网客户端连接）
  - 3000/tcp：Mineflayer HTTP 接口
  - 22/tcp：SSH 管理

在云平台“安全组/防火墙”中开放所需端口（最少 22，通常还需要 3000；如需外网玩家连接 Minecraft，再开放 25565）。

---

## 2. 实例与系统建议

- 系统：Ubuntu 22.04 LTS（推荐）；也可使用 Windows Server，但本文以 Linux 为主
- 规格建议（基础）：
  - vCPU：4 核+
  - 内存：8–16 GB（Minecraft 服务器越吃内存）
  - 磁盘：50 GB+
- GPU：非必须（本仓库默认调用云端大模型 API，如 OpenAI 或阿里云百炼 DashScope）。如需要自部署大模型，请按需加配 GPU 并另行部署推理服务。

---

## 3. 基础环境安装（Ubuntu）

更新系统并安装常用工具：

```bash
sudo apt update && sudo apt -y upgrade
sudo apt -y install git curl wget unzip tmux build-essential
```

安装 Java 17（Minecraft 1.19/Fabric 推荐 Java 17）：

```bash
sudo apt -y install openjdk-17-jdk
java -version
```

安装 Node.js LTS（18+）：

```bash
# 使用 NodeSource（示例为 Node 20 LTS）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt -y install nodejs
node -v
npm -v
```

安装 uv（Python 包管理/环境工具）与 Python：

```bash
# 安装 uv（官方脚本）
curl -LsSf https://astral.sh/uv/install.sh | sh
# 重新加载 shell，或执行：
export PATH="$HOME/.local/bin:$PATH"

# 安装 Python（例如 3.12），并设置为项目使用版本
uv python install 3.12
uv python list
```

---

## 4. 获取代码与安装依赖

```bash
# 选定部署目录，例如 /opt
sudo mkdir -p /opt && sudo chown $USER:$USER /opt
cd /opt

# 拉取代码（如已上传到私有仓库，请配置 SSH Key 或 Token）
git clone https://github.com/MineDojo/Voyager.git
cd Voyager

# 同步 Python 依赖（生成 .venv 虚拟环境）
uv sync

# 安装 Mineflayer 依赖
cd voyager/env/mineflayer
npm install
cd ../../../
```

> 注意：本仓库已适配较新的 LangChain 包拆分；如你使用自有分支，请以 `uv sync` 的结果为准。

---

## 5. 配置密钥与环境变量

Voyager 运行需要以下可选/必选密钥：

- OpenAI：`OPENAI_API_KEY`
- 阿里云 DashScope（用于 QwQ/通义）：`DASHSCOPE_API_KEY`
- Microsoft OAuth（Minecraft 官方登录）：在首次运行时会提示登录，需准备 Azure 应用的 `client_id`、`secret_value`、`redirect_url`

推荐使用环境变量方式而不是在 `run.py` 明文写入：

```bash
# 示例：在 bash 中临时导出（也可写入 ~/.bashrc）
export OPENAI_API_KEY="sk-..."
export DASHSCOPE_API_KEY="sk-..."

# 供 Minecraft 登录用——首次运行会用到
echo '请在 run.py 中配置 azure_login（client_id/secret/redirect_url/version）'
```

如果你不希望修改代码，可直接按仓库现有的 `run.py` 格式填写 `azure_login` 字段，但注意不要将密钥提交到仓库。

阿里云 DashScope 开通与 Key 获取：
- 控制台入口：百炼（DashScope）平台
- 创建 API Key 后填入 `DASHSCOPE_API_KEY`

腾讯云若使用第三方模型服务，请按对应服务商的 Key 配置为环境变量，并在代码/配置中替换调用位置。

---

## 6. 运行与后台常驻

### 6.1 先启动 Mineflayer 桥接服务

```bash
cd /opt/Voyager/voyager/env/mineflayer
node index.js  # 默认 3000 端口
```

建议使用 `tmux` 或 `pm2` 守护：

```bash
# tmux 方式
sudo apt -y install tmux
cd /opt/Voyager/voyager/env/mineflayer
tmux new -s mineflayer -d "node index.js"
# 查看日志
tmux attach -t mineflayer
```

或使用 `pm2`：

```bash
sudo npm i -g pm2
cd /opt/Voyager/voyager/env/mineflayer
pm2 start index.js --name mineflayer
pm2 save
pm2 startup  # 按提示设置开机自启
```

### 6.2 启动 Voyager（Python）

```bash
cd /opt/Voyager
# 激活虚拟环境并运行
source .venv/bin/activate
python run.py
```

首次运行会打印 Microsoft 登录 URL：
1. 复制终端中出现的登录链接，在本地浏览器打开并完成登录授权。
2. 授权后浏览器会跳转到你配置的 `redirect_url`，将地址栏完整 URL 复制回服务器终端回车。
3. 程序会完成 token 交换并启动 Minecraft 服务器与代理。

---

## 7. 云平台安全组/防火墙（阿里云/腾讯云要点）

- 阿里云 ECS：
  - 控制台 > ECS 实例 > 网络与安全组 > 安全组规则
  - 入方向放通：22（管理）、3000（Mineflayer）、25565（如需对外开放 Minecraft）
- 腾讯云 CVM：
  - 控制台 > 云服务器 > 安全组
  - 入站规则添加相同端口；如绑定了弹性公网 IP（EIP），注意同时检查 VPC 或操作系统防火墙（ufw）

OS 级别防火墙（可选）：
```bash
sudo ufw allow 22/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 25565/tcp  # 如需对外开放 Minecraft
sudo ufw enable
sudo ufw status
```

---

## 8. 日志位置与排错

- Mineflayer 日志：`logs/mineflayer/`
- Minecraft 服务器日志：`logs/minecraft/`
- 常见错误：
  - `EADDRINUSE: 3000`：端口被占用。处理：找出占用进程或改用 `node index.js 4000` 并在 Python 侧（如有）对应调整。
  - `KeyError: 'access_token'`：Microsoft OAuth 未正确交换 token。检查 `client_id/secret/redirect_url` 是否匹配应用登记；密钥是否过期；复制回终端的重定向 URL 是否完整无误。
  - Java 版本不兼容：确保 `java -version` 为 17（或与 Fabric/模组要求一致）。
  - 端口不可达：检查云安全组、OS 防火墙与进程是否已监听。

---

## 9. 可选：使用 systemd 开机自启

以 pm2/tmux 更简单；若需 systemd：

示例 mineflayer 单元 `/etc/systemd/system/mineflayer.service`：
```ini
[Unit]
Description=Voyager Mineflayer Service
After=network.target

[Service]
Type=simple
User=%i
WorkingDirectory=/opt/Voyager/voyager/env/mineflayer
ExecStart=/usr/bin/node /opt/Voyager/voyager/env/mineflayer/index.js
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

示例 voyager 单元 `/etc/systemd/system/voyager.service`：
```ini
[Unit]
Description=Voyager Python Controller
After=network.target mineflayer.service

[Service]
Type=simple
User=%i
WorkingDirectory=/opt/Voyager
Environment=OPENAI_API_KEY=你的key
Environment=DASHSCOPE_API_KEY=你的key
ExecStart=/opt/Voyager/.venv/bin/python /opt/Voyager/run.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

加载与启动：
```bash
sudo systemctl daemon-reload
sudo systemctl enable mineflayer --now
sudo systemctl enable voyager --now
sudo systemctl status mineflayer voyager
```

---

## 10. 阿里云与腾讯云差异要点

- 安全组规则添加路径不同，但概念一致：都需放通 22/3000/25565（按需）。
- 弹性公网 IP（EIP）与带宽计费策略不同；长时间运行建议观察公网流量费用。
- 监控/告警：
  - 阿里云：`云监控` 可对 CPU/内存/端口做告警。
  - 腾讯云：`云监控` 同理；也可用 `日志服务 CLS` 聚合日志。

---

## 11. FAQ

- Q：能完全不使用 Azure 平台吗？
  - A：计算资源完全可使用阿里/腾讯云；但 Minecraft 官方登录仍依赖 Microsoft OAuth（其授权端点在 Azure AD），因此仍需一个可用的应用注册与 `client_id/secret/redirect_url`。
- Q：能否使用阿里云百炼（DashScope）替代 OpenAI？
  - A：可以。项目已支持 `langchain-qwq` 与 `DASHSCOPE_API_KEY`，根据你的模型选择调整 `model_name` 即可。
- Q：如何持久化与备份？
  - A：建议将 `logs/`、`skill_library/` 与 `ckpt/`（若存在）打包到对象存储（OSS/COS），或快照磁盘。

---

祝部署顺利。如需将密钥改为纯环境变量读取、或需要提供现成的 systemd/pm2 配置文件模板，请在 Issue 中提出，我们可以进一步补充。