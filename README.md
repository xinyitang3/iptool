---

# Cloudflare IP 优选工具

[![GitHub stars](https://img.shields.io/github/stars/xinyitang3/cfnb?style=social)](https://github.com/xinyitang3/cfnb/stargazers)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()
[![Last Commit](https://img.shields.io/github/last-commit/xinyitang3/cfnb?label=Last%20Commit)](https://github.com/xinyitang3/cfnb/commits)
[![Repo Size](https://img.shields.io/github/repo-size/xinyitang3/cfnb?label=Repo%20Size)](https://github.com/xinyitang3/cfnb)

> ⭐ **如果觉得好用，点个 Star 支持一下～**

这是一个全自动的 **Cloudflare CDN 节点优选工具**。它通过 **TCP 延迟筛选** + **IP 可用性二次检测** + **真实带宽测速** + **IP 纯净度过滤** 四重机制，从海量公开节点中筛选出当前网络环境下速度最快、可用性最高、滥用评分最低的 Cloudflare IP，并支持**自动更新至 Cloudflare DNS** 以及**同步至 GitHub 仓库**，同时支持微信实时通知。

> [!IMPORTANT]
> **跨平台支持**：本工具同时兼容 **Windows** 和 **Linux** 操作系统。
> - Windows 自动推送依赖 PowerShell 脚本 `git_sync.ps1`
> - Linux 自动推送依赖 Bash 脚本 `git_sync.sh`

---

### 📍 快速导航
- 🚀 [我要部署](#-部署步骤)（Windows / Linux 命令对照）
- 🔐 [我要获取 Token](#-获取必要令牌重要)（GitHub / Cloudflare / WxPusher 三合一教程）
- ⚙️ [我要调整参数](#%EF%B8%8F-配置说明完整参数详解)
- ☁️ [我要配置 Cloudflare DNS](#-配置-cloudflare-dns-自动更新)
- 📤 [我要配置 GitHub 同步](#-配置-github-自动同步)
- 🔗 [对接 EdgeTunnel 指南](#-%E5%AF%B9%E6%8E%A5-edgetunnel-20-%E6%8C%87%E5%8D%97)
- ❓ [常见问题](#-常见问题)

---

## ✨ 功能特性

| 模块 | 说明 |
| :--- | :--- |
| 🌐 **多模式筛选** | 全局最优 TopN / 分国家最优 TopN |
| ⚡ **TCP 连接测试** | 并发测延迟，可设成功率阈值 |
| 🔍 **可用性二次检测** | 调用 API 验证代理能力，记录落地 IP |
| 📶 **真实带宽测速** | curl 下载测速文件，实测吞吐量 |
| 🛡️ **IP 纯净度过滤** | 过滤滥用评分非 Low 的 IP |
| 🌍 **国家过滤前置** | TCP 测试前即过滤指定国家节点 |
| ☁️ **Cloudflare DNS 更新** | 批量替换同名 A 记录，仅保留落地 IPv4 |
| 📬 **微信实时通知** | 集成 WxPusher，异常/结果推送 |
| 🔄 **定时自动运行** | Windows 计划任务 / Linux cron，每 15 分钟 |
| 🚀 **一键部署** | `setup.ps1` / `setup.sh` 自动安装依赖并配置 |
| 📤 **GitHub 自动同步** | `ip.txt` 推送至仓库，方便订阅 |
| 🔒 **隐私保护** | `.gitignore` 忽略敏感文件 |
| 🖥️ **跨平台兼容** | 同时支持 Windows 和 Linux |

---

## 📦 文件清单

| 文件 | 说明 |
| :--- | :--- |
| `main.py` | 核心优选程序（抓取、测试、筛选、更新、推送） |
| `config.json` | 所有运行参数的配置文件（含详细注释） |
| `git_sync.ps1` | Windows 推送脚本（强制推送 `ip.txt` 到 GitHub） |
| `git_sync.sh` | Linux 推送脚本（强制推送 `ip.txt` 到 GitHub） |
| `setup.ps1` | Windows 一键部署脚本（安装依赖并配置计划任务） |
| `setup.sh` | Linux 一键部署脚本（安装依赖并配置 cron） |
| `ip.txt` | 最终优选节点列表（每次运行覆盖） |

---

## 🖥️ 系统要求

- **操作系统**：Windows 10+ / Windows Server 2016+ 或 Linux（Ubuntu/Debian/CentOS 等）
- **必备软件**：
  - **Python 3.7+**
  - **Git**
  - **curl**（需在系统 PATH 中可用）
- **Python 依赖**：`requests` 库

---

## 🚀 部署步骤

### 通用前置步骤

1. **获取项目文件**  
   ```bash
   git clone https://github.com/你的用户名/仓库名.git
   cd 仓库名
   ```

2. **配置各项令牌（见下一节）**  
   根据需求获取并填写 GitHub Token、Cloudflare API Token 和 WxPusher 凭证。

3. **（可选）关闭不需要的功能**  
   - 无需微信通知：`config.json` 中设 `ENABLE_WXPUSHER: false`  
   - 无需 GitHub 推送：`config.json` 中设 `GITHUB_SYNC_MAX_RETRIES: 0`  
   - 无需 Cloudflare DNS 更新：`config.json` 中设 `CF_ENABLED: false`

---

### 🔐 获取必要令牌（重要）

若您希望启用 GitHub 自动推送、Cloudflare DNS 更新或微信通知，请参考下表获取对应令牌。

| GitHub Personal Access Token | Cloudflare API Token | WxPusher 微信通知 |
| :---: | :---: | :---: |
| **1.** 登录 GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) | **1.** 登录 Cloudflare → My Profile → API Tokens → Create Token → Create Custom Token | **1.** 访问 [WxPusher 后台](http://wxpusher.zjiecode.com/admin/)，微信扫码登录 |
| **2.** Generate new token (classic)，Note 任意填 | **2.** Token name 任意；Permissions: `Zone` → `DNS` → `Edit`；Zone Resources: 选择你的域名 | **2.** 左侧菜单“应用管理”→“应用信息”→“新增应用”，填写名称后创建 |
| **3.** **Expiration 必须选 `No expiration`** | **3.** 点击 Continue to summary → Create Token | **3.** 复制保存 **AppToken**（仅显示一次） |
| **4.** Select scopes: 仅勾选 **repo**（自动勾全） | **4.** **立即复制保存 Token** | **4.** 左侧“关注应用”→微信扫码关注公众号 |
| **5.** Generate token，**立即复制保存** | **5.** Zone ID 在域名概览页右侧“API”栏目复制 | **5.** 公众号菜单“我的”→“我的UID”获取 UID |
| 填入 `git_sync.ps1` / `git_sync.sh` 的 `github_token` | 填入 `config.json` 的 `CF_API_TOKEN` 和 `CF_ZONE_ID` | 填入 `config.json` 的 `WXPUSHER_APP_TOKEN` 和 `WXPUSHER_UIDS` |

> 💡 若不需要某项功能，可跳过对应步骤或在配置中关闭开关。

---

### Windows 部署

| 步骤 | 操作 |
| :--- | :--- |
| **启动管理员 PowerShell** | 按 `Win + X`，选择 **“Windows PowerShell (管理员)”** 或 **“终端 (管理员)”** |
| **进入项目目录** | `cd "C:\你的项目路径\cfnb"` |
| **解除执行限制（如需要）** | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| **运行部署脚本** | `.\setup.ps1` |
| **编辑推送脚本** | 编辑 `git_sync.ps1`，填入 GitHub 令牌等信息 |
| **测试运行** | `python main.py` |

脚本自动完成：安装 Python/Git/curl、requests 库、创建 .gitignore、配置计划任务（下个整 15 分开始，无限期重复）。

### Linux 部署

| 步骤 | 操作 |
| :--- | :--- |
| **进入项目目录** | `cd /path/to/cfnb` |
| **赋予执行权限** | `chmod +x setup.sh` |
| **运行部署脚本** | `sudo ./setup.sh` |
| **编辑推送脚本** | 编辑 `git_sync.sh`，填入 GitHub 令牌等信息 |
| **测试运行** | `python3 main.py` |

脚本自动完成：检测包管理器安装 Python3/pip/Git/curl、requests 库、创建 .gitignore、配置 cron 定时任务（整点 15 分对齐）。

<details>
<summary>📝 手动部署详细步骤（点击展开）</summary>

#### Windows 手动部署

1. 安装 [Python 3](https://www.python.org/downloads/)（勾选 “Add Python to PATH”）。
2. 安装 [Git](https://git-scm.com/download/win) 和 [curl](https://curl.se/windows/)（curl 需加入 PATH）。
3. 在项目目录打开命令提示符，安装依赖：
   ```cmd
   pip install requests
   ```
4. （可选）手动创建计划任务：
   - 按 `Win + R`，输入 `taskschd.msc` 打开任务计划程序。
   - 创建任务，名称 `Cloudflare IP 优选`，勾选“不管用户是否登录都要运行”和“使用最高权限运行”。
   - 触发器：新建 → 开始任务“按预定计划” → 设置“一次”，开始时间为下一个整15分钟时刻；高级设置中勾选“重复任务间隔”，选择“15分钟”，持续时间“无限期”。
   - 操作：新建 → 操作“启动程序”，程序填写 `python.exe` 路径，参数填写 `main.py` 完整路径，起始于填写项目目录。

#### Linux 手动部署

1. 安装系统依赖（以 Debian/Ubuntu 为例）：
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip git curl
   ```
2. 安装 Python 依赖：
   ```bash
   pip3 install requests
   ```
3. 赋予推送脚本执行权限（如果需要）：
   ```bash
   chmod +x git_sync.sh
   ```
4. （可选）添加 cron 任务：
   ```bash
   (crontab -l 2>/dev/null; echo "0,15,30,45 * * * * cd $(pwd) && /usr/bin/python3 $(pwd)/main.py >> $(pwd)/cron.log 2>&1") | crontab -
   ```
5. 验证：`crontab -l`

</details>

---

## 🕒 定时自动运行说明

| 平台 | 方式 | 行为 |
| :--- | :--- | :--- |
| Windows | 计划任务 `Cloudflare IP 优选` | 从下一个整 15 分钟开始，之后每 15 分钟**永久重复** |
| Linux | cron 定时任务 | 分钟字段 `0,15,30,45`，整点对齐 |

**日志查看**：
- Windows：任务计划程序中查看历史记录。
- Linux：`tail -f cron.log`

---

## ⚙️ 配置说明（完整参数详解）

> [!NOTE]
> 默认参数基于 **2核2G 云服务器** 测试通过。若在 **软路由、树莓派或低配 PC** 上运行，建议降低 `MAX_WORKERS`、`BANDWIDTH_WORKERS`。

### 筛选模式与数量控制

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `USE_GLOBAL_MODE` | `boolean` | `true` | `true`=全局优选；`false`=分国家优选 |
| `GLOBAL_TOP_N` | `int` | `16` | 全局模式保留节点数 |
| `PER_COUNTRY_TOP_N` | `int` | `1` | 分国家模式每国保留节点数 |
| `BANDWIDTH_CANDIDATES` | `int` | `80` | 进入测速的候选节点数 |

### TCP 连接测试参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `TCP_PROBES` | `int` | `7` | 每个节点 TCP 测试次数 |
| `MIN_SUCCESS_RATE` | `float` | `1.0` | 最低成功率阈值（0.0~1.0） |
| `TIMEOUT` | `float` | `2.5` | 单次 TCP 连接超时（秒） |

### 国家过滤参数（前置优化）

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `FILTER_COUNTRIES_ENABLED` | `boolean` | `false` | 是否启用国家过滤 |
| `ALLOWED_COUNTRIES` | `array` | `["US","HK"]` | 允许的国家代码列表 |

### 微信通知（WxPusher）参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `ENABLE_WXPUSHER` | `boolean` | `true` | 是否启用微信通知 |
| `WXPUSHER_APP_TOKEN` | `string` | `""` | **【必填】** WxPusher 的 APP_TOKEN |
| `WXPUSHER_UIDS` | `array` | `[""]` | **【必填】** 接收通知的用户 UID 列表 |
| `WXPUSHER_API_URL` | `string` | `http://wxpusher.zjiecode.com/api/send/message` | 消息发送 API 地址 |

> 💡 若不需要通知，将 `ENABLE_WXPUSHER` 设为 `false` 即可。

### Cloudflare DNS 批量更新参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `CF_ENABLED` | `boolean` | `true` | 是否启用 DNS 自动更新 |
| `CF_API_TOKEN` | `string` | `"your_CF_API_TOKEN"` | Cloudflare API 令牌（Zone:DNS:Edit 权限） |
| `CF_ZONE_ID` | `string` | `"your_CF_ZONE_ID"` | 域名区域 ID |
| `CF_DNS_RECORD_NAME` | `string` | `"your_CF_DNS_RECORD_NAME"` | 完整子域名 |
| `CF_TTL` | `int` | `60` | DNS 记录 TTL（秒） |
| `CF_PROXIED` | `boolean` | `false` | 是否启用 Cloudflare CDN 代理 |

> 💡 若不需要 DNS 更新，将 `CF_ENABLED` 设为 `false` 即可。

### 节点数据源与输出

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `JSON_URL` | `string` | `"https://zip.cm.edu.kg/all.txt"` | Cloudflare IP 节点数据源 |
| `OUTPUT_FILE` | `string` | `"ip.txt"` | 最终结果保存文件名 |

<details>
<summary>🔧 高级参数（可用性 / 带宽 / 纯净度 / 并发 / 重试）</summary>

### 可用性检测参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `TEST_AVAILABILITY` | `boolean` | `true` | 是否进行可用性二次筛选 |
| `FILTER_IPV6_AVAILABILITY` | `boolean` | `true` | DNS 更新时是否过滤落地 IPv6 |
| `AVAILABILITY_CHECK_API` | `string` | `"https://check-proxyip-api.cmliussss.net/check"` | 可用性检测 API 地址 |
| `AVAILABILITY_TIMEOUT` | `float` | `8` | 单次 API 请求超时（秒） |
| `AVAILABILITY_RETRY_MAX` | `int` | `2` | 可用性检测最大重试轮数 |
| `AVAILABILITY_RETRY_DELAY` | `int` | `5` | 可用性检测重试间隔（秒） |

### 带宽测速参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `BANDWIDTH_SIZE_MB` | `int` | `1` | 测速下载文件大小（MB） |
| `BANDWIDTH_TIMEOUT` | `float` | `5` | 单个节点带宽测速超时（秒） |
| `BANDWIDTH_RETRY_MAX` | `int` | `2` | 带宽测速整体重试轮数 |
| `BANDWIDTH_RETRY_DELAY` | `int` | `5` | 带宽测速重试间隔（秒） |
| `BANDWIDTH_URL_TEMPLATE` | `string` | `"https://speed.cloudflare.com/__down?bytes={bytes}"` | 测速 URL 模板 |

### 纯净度检测参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `ENABLE_IP_PURITY_CHECK` | `boolean` | `true` | 是否进行 IP 纯净度检测 |
| `IP_PURITY_API` | `string` | `"https://api.ipapi.is/"` | 纯净度检测 API 地址 |
| `IP_PURITY_WORKERS` | `int` | `10` | 纯净度检测并发数 |
| `IP_PURITY_TIMEOUT` | `int` | `8` | 纯净度 API 请求超时（秒） |
| `IP_PURITY_RETRY_MAX` | `int` | `2` | 纯净度检测最大重试轮数 |
| `IP_PURITY_RETRY_DELAY` | `int` | `5` | 纯净度检测重试间隔（秒） |
| `IP_PURITY_FALLBACK` | `boolean` | `true` | 全部失败时是否降级 |

### 并发控制参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `MAX_WORKERS` | `int` | `150` | TCP 并发测试最大线程数 |
| `AVAILABILITY_WORKERS` | `int` | `20` | 可用性检测并发数 |
| `BANDWIDTH_WORKERS` | `int` | `6` | 带宽测速并发数（建议不超过 10） |

### 重试策略配置

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `DNS_UPDATE_MAX_RETRIES` | `int` | `5` | DNS 更新最大重试次数 |
| `DNS_UPDATE_RETRY_DELAY` | `int` | `10` | DNS 更新重试间隔（秒） |
| `GITHUB_SYNC_MAX_RETRIES` | `int` | `5` | GitHub 推送最大重试次数 |
| `GITHUB_SYNC_RETRY_DELAY` | `int` | `10` | GitHub 推送重试间隔（秒） |

</details>

> 💡 **快速配置建议**  
> - 通常只需修改 `ALLOWED_COUNTRIES`、`WXPUSHER_APP_TOKEN`、`WXPUSHER_UIDS`。  
> - 启用 DNS 更新需正确填写 `CF_API_TOKEN`、`CF_ZONE_ID`、`CF_DNS_RECORD_NAME`。  
> - 网络不稳定时可 ↑ `TCP_PROBES` / `TIMEOUT`，↓ `MIN_SUCCESS_RATE` / `MAX_WORKERS`。  
> - 希望更快出结果可 ↓ `BANDWIDTH_CANDIDATES` 或 `BANDWIDTH_SIZE_MB`。

---

## 📊 结果输出说明

程序运行完成后，会在本地生成 `ip.txt` 并在同步后更新至 GitHub 链接：
`https://raw.githubusercontent.com/你的用户名/仓库名/refs/heads/分支名/ip.txt`

### 文件格式
`ip.txt` 采用标准格式，每一行代表一个最优节点，具体格式为：
`IP地址:端口#国家代码`

> **示例：**
> `104.16.x.x:443#US`
> `162.159.x.x:443#HK`

---

## ☁️ 配置 Cloudflare DNS 自动更新

本工具支持将优选出的 IP 地址列表自动更新到 Cloudflare DNS 的同名 A 记录，实现解析层面的多 IP 轮询负载均衡。

### 第一步：获取 Cloudflare API Token 与 Zone ID

1. 按照 [获取必要令牌](#-获取必要令牌重要) 中的步骤获取 **Cloudflare API Token**（需具有 Zone:DNS:Edit 权限）。
2. 在 Cloudflare 域名概览页面右侧复制您的 **Zone ID**。

### 第二步：填写配置文件

编辑 `config.json`，找到 Cloudflare DNS 配置部分，填入您的信息：

```json
"CF_ENABLED": true,
"CF_API_TOKEN": "your_CF_API_TOKEN",
"CF_ZONE_ID": "your_CF_ZONE_ID",
"CF_DNS_RECORD_NAME": "your-domain.example.com",
"CF_TTL": 60,
"CF_PROXIED": false
```

| 参数 | 说明 |
|------|------|
| `CF_ENABLED` | 设为 `true` 启用 DNS 自动更新 |
| `CF_API_TOKEN` | 上一步获取的 API Token |
| `CF_ZONE_ID` | 上一步获取的 Zone ID |
| `CF_DNS_RECORD_NAME` | 要更新的完整子域名 |
| `CF_TTL` | DNS 记录 TTL（秒），免费套餐最低 120 |
| `CF_PROXIED` | 是否启用 Cloudflare CDN 代理（橙色云朵），通常设为 `false` |

> 💡 若不需要 DNS 更新功能，将 `CF_ENABLED` 设为 `false` 即可。

### 第三步：测试运行

1. 手动运行一次优选程序：`python main.py`（Windows）或 `python3 main.py`（Linux）。
2. 程序运行结束后，观察控制台输出。若看到 `✅ Cloudflare DNS 批量更新成功！`，则配置成功。

### 工作原理

每次运行时，脚本会：

1. 查询目标子域名下现有的所有 A 记录。
2. 从带宽测速结果中按速度顺序挑选落地 IPv4 的节点（若启用 `FILTER_IPV6_AVAILABILITY`）。
3. 利用 Cloudflare 批量 API **先删除所有旧记录，再创建新记录**，实现原子替换。

### 注意事项

- 免费套餐单次批量操作最多支持 200 条记录，足够使用。
- 若候选池中落地 IPv4 节点不足目标数量，则更新实际可用的数量，不会强制凑满。
- 全量替换在极短时间内可能导致解析短暂为空，但对绝大多数场景无影响。
- 若需完全避免服务中断，可自行修改代码为增量更新（只增删差异部分）。
```

---

## 📤 配置 GitHub 自动同步

本工具支持每次运行后将 `ip.txt` 自动推送到您指定的 GitHub 仓库，方便通过 Raw 链接订阅节点列表。

### 第一步：创建 GitHub 仓库

1. 登录 GitHub，点击右上角 `+` → **New repository**。
2. **Repository name** 可任意填写（如 `cf-ip`）。
3. 仓库类型选择 **Private**（推荐）或 Public。
4. **不要**勾选 “Add a README file”、“.gitignore” 等初始化选项。
5. 点击 **Create repository**。

### 第二步：初始化本地仓库并关联远程

在项目根目录下打开终端（Windows 为 PowerShell，Linux 为终端），依次执行以下命令：

```bash
git init
git remote add origin https://github.com/你的用户名/仓库名.git
git branch -M main
```

> 💡 如果您是通过 `git clone` 命令下载的本项目，则本地仓库已自动关联远程，无需执行上述命令，直接跳到第三步。

### 第三步：获取并填写 GitHub Token

1. 按照 [获取必要令牌](#-获取必要令牌重要) 中的步骤获取 **GitHub Personal Access Token**（需勾选 `repo` 权限，过期时间设为 **No expiration**）。
2. 编辑对应平台的推送脚本：
   - **Windows**：用文本编辑器打开 `git_sync.ps1`
   - **Linux**：用文本编辑器打开 `git_sync.sh`
3. 将脚本开头部分的四个变量替换为您的真实信息：

   ```powershell
   # Windows (git_sync.ps1)
   $github_token = "ghp_xxxxxxxxxxxxxxxxxxxx"
   $github_username = "your_github_username"
   $repo_name = "your_repo_name"
   $branch = "main"
   ```

   ```bash
   # Linux (git_sync.sh)
   github_token="ghp_xxxxxxxxxxxxxxxxxxxx"
   github_username="your_github_username"
   repo_name="your_repo_name"
   branch="main"
   ```

### 第四步：测试推送

1. 确保项目目录下已有 `ip.txt` 文件（可先手动运行一次 `python main.py` 生成）。
2. 手动执行推送脚本测试：
   - **Windows**：双击运行 `git_sync.ps1` 或在 PowerShell 中执行 `.\git_sync.ps1`
   - **Linux**：执行 `./git_sync.sh`
3. 若终端显示 `✅ ip.txt 已推送到 GitHub`，则配置成功。
4. 之后每次运行 `main.py`，程序都会自动调用推送脚本，无需人工干预。

### 验证与订阅

推送成功后，访问 `https://raw.githubusercontent.com/你的用户名/仓库名/refs/heads/分支名/ip.txt` 即可获取最新节点列表，供代理工具订阅使用。

> 💡 若不需要 GitHub 同步功能，可在 `config.json` 中设置 `GITHUB_SYNC_MAX_RETRIES: 0` 即可关闭。

---


## 🚀 对接 EdgeTunnel (2.0+) 指南

**EdgeTunnel** (EDTunnel) 是基于 Cloudflare Workers 的隧道工具。使用本项目筛选出的 `ip.txt` 可以显著提升连接速度和稳定性。

### 方法一：优选订阅模式（推荐）

1. 复制你的 GitHub Raw 链接：
   ```
   https://raw.githubusercontent.com/你的用户名/仓库名/refs/heads/分支名/ip.txt
   ```
2. 打开 EdgeTunnel 控制面板，点击菜单栏的 **“优选订阅生成”**。
3. 在 **“优选订阅模式”** 区域，选择 **“自定义订阅（支持汇聚订阅）”**。
4. 点击 **“订阅接口”** 按钮，在 **API URL** 输入框中粘贴上一步获取的 GitHub Raw 链接。
   > 💡 如需指定端口，可在链接后添加 `?port=443`。
5. （可选）勾选 **“将优选作为 PROXYIP”**。
6. 点击 **“可用性验证”**，系统将验证 API 并拉取节点列表。
7. 检查无误后，点击 **“追加API”** 按钮将链接加入自定义订阅地址。
8. 点击 **“保存”** 按钮完成配置。

### 方法二：手动替换 EdgeTunnel 节点配置

1. 打开 EdgeTunnel 控制面板，点击菜单栏的 **“优选订阅生成”**。
2. 在 **“优选订阅模式”** 区域，选择 **“自定义订阅（支持汇聚订阅）”**。
3. 在 **“自定义订阅地址”** 输入框中直接粘贴节点地址，每行一个，例如：
   ```
   104.16.x.x:443#US
   162.159.x.x:443#HK
   ```
4. 点击 **“保存”** 按钮，即可手动指定优选的节点列表。

### 方法三：使用 Cloudflare DNS 域名（最新功能）

如果您已启用 Cloudflare DNS 批量更新，可以直接将您的子域名（如 `你的域名.dpdns.org`）填入 EdgeTunnel：

**方式一：通过“优选订阅生成”**
1. 打开 **“优选订阅生成”** 页面，选择 **“自定义订阅（支持汇聚订阅）”**。
2. 在 **“自定义订阅地址”** 输入框中，填入您的子域名（例如 `你的域名.dpdns.org`）。
3. 点击 **“保存”** 按钮。

**方式二：通过“Cloudflare CDN 访问设置”**
1. 进入 **“Cloudflare CDN 访问设置”** 页面。
2. 在 **“PROXYIP”** 输入框中，填入您的子域名（例如 `你的域名.dpdns.org`）。
3. 点击 **“保存”** 按钮。

该域名会自动解析到当前最优的多个 IP 之一，实现零配置动态切换。

### 💡 为什么这样对接更有效？
- **低延迟**：`main.py` 已经通过 TCP 握手筛选出了延迟最低的节点。
- **高带宽**：结果经过真实 `curl` 下载测试，排在前面的节点具有更强的并发吞吐能力。
- **高可用**：通过 `AVAILABILITY_CHECK_API` 过滤了那些能 Ping 通但无法正常通过代理请求的无效 IP。
- **高纯净度**：通过 `ipapi.is` 排除了被标记为滥用的 IP，降低被目标网站屏蔽的风险。
- **自动更新**：DNS 记录随优选结果自动刷新，无需手动修改配置。

### 注意事项
- **GitHub 缓存**：GitHub Raw 链接有一定的 CDN 缓存时间（通常为 5 分钟左右）。如果刚运行完脚本发现链接内容没变，请稍等片刻。
- **网络环境**：建议在你的主运行环境（如家庭软路由或主力 PC）运行此脚本，因为不同网络环境下筛选出的最优 IP 可能不同。
- **DNS 生效时间**：修改 DNS 记录后受 TTL 影响，全球生效可能需要几分钟，但通常 Cloudflare 更新是实时的。

---

## ❓ 常见问题

<details>
<summary>🔌 依赖与安装</summary>

1. **提示 `ModuleNotFoundError: No module named 'requests'`**  
   请执行 `pip install requests` (Windows) 或 `pip3 install requests` (Linux)。

2. **带宽测速被跳过**  
   请确保系统已安装 `curl` 且位于 PATH 环境变量中。

3. **Linux 下 `git_sync.sh` 权限被拒绝**  
   执行 `chmod +x git_sync.sh` 赋予执行权限。

</details>

<details>
<summary>📤 GitHub 推送与同步</summary>

4. **GitHub 推送失败**  
   - 检查 `git_sync.ps1` / `git_sync.sh` 中的 Token、用户名、仓库名是否正确。
   - 确保 Token 具备 `repo` 权限。
   - 确认本地 Git 已正确配置用户信息（`git config --global user.name/email`）。

5. **GitHub 推送时提示权限错误或 403**  
   - 请确认令牌具有 `repo` 权限，且未过期。创建令牌时务必勾选 **repo** 全部子项，并将过期时间设为 **No expiration**。

</details>

<details>
<summary>☁️ Cloudflare DNS 更新</summary>

6. **Cloudflare DNS 更新失败**  
   - 检查 `CF_API_TOKEN` 是否有效且具有 Zone:DNS:Edit 权限。
   - 检查 `CF_ZONE_ID` 是否正确。
   - 检查 `CF_DNS_RECORD_NAME` 是否为完整的子域名且已托管在 Cloudflare。
   - 脚本自带 5 次重试机制，若全部失败会通过微信通知。

7. **为什么我的 DNS 记录数量少于 `GLOBAL_TOP_N`？**  
   如果您启用了 `FILTER_IPV6_AVAILABILITY`，且候选池中落地 IPv4 的节点总数不足目标数量，则 DNS 只会更新实际可用的节点数。这是正常现象，您可以通过增加 `BANDWIDTH_CANDIDATES` 来扩大候选池。

</details>

<details>
<summary>🔍 检测与过滤</summary>

8. **可用性检测或纯净度检测全部失败**  
   若 API 接口异常，程序会自动跳过此步骤并回退到 TCP 筛选结果，同时发送微信提醒（如已配置）。纯净度检测还可通过 `IP_PURITY_FALLBACK` 控制是否降级。

</details>

<details>
<summary>🔒 隐私与其他</summary>

9. **隐私保护**  
   自动生成的 `.gitignore` 文件会忽略 `config.json`、`git_sync.ps1` 和 `git_sync.sh`，防止敏感信息被提交到公开仓库。

</details>

---

## 🙏 致谢

- 节点数据源 & 检测 API：[cmliussss](https://github.com/cmliussss)
- 微信通知服务：[WxPusher](https://wxpusher.zjiecode.com/)
- IP 纯净度检测：[ipapi.is](https://ipapi.is/)

---

**许可证**：本项目采用 [MIT License](https://opensource.org/licenses/MIT) 开源。

---
