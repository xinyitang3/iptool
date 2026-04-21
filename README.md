---

# Cloudflare IP 优选工具

[![GitHub stars](https://img.shields.io/github/stars/xinyitang3/cfnb?style=social)](https://github.com/xinyitang3/cfnb/stargazers)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

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
- ⚙️ [我要调整参数](#%EF%B8%8F-配置说明完整参数详解)（所有参数原封保留）
- ☁️ [我要配置 DNS 更新](#%EF%B8%8F-cloudflare-dns-批量更新说明)
- ❓ [我遇到问题了](#-常见问题)（按类别折叠）

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
| `main.py` | **核心程序**：负责抓取节点、TCP 测试、可用性检测、带宽测速、纯净度检测、保存结果、更新 DNS、推送 GitHub。 |
| `config.json` | **配置文件**：所有运行参数均在此修改（含详细注释）。 |
| `git_sync.ps1` | **Windows 推送脚本**：用于将 `ip.txt` 强制推送到 GitHub。 |
| `git_sync.sh` | **Linux 推送脚本**：用于将 `ip.txt` 强制推送到 GitHub。 |
| `setup.ps1` | **Windows 一键部署脚本**：自动安装依赖、配置计划任务（需管理员权限）。 |
| `setup.sh` | **Linux 一键部署脚本**：自动安装依赖、配置 cron 定时任务（需 root 权限）。 |
| `ip.txt` | **输出结果**：程序运行后生成的优选节点列表（每次运行会覆盖）。 |

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
   通过 Git 克隆或直接下载 ZIP 压缩包并解压：
   ```bash
   git clone https://github.com/你的用户名/仓库名.git
   cd 仓库名
   ```

2. **配置微信通知（可选）**  
   编辑 `config.json`，填写 WxPusher 的 `WXPUSHER_APP_TOKEN` 和 `WXPUSHER_UIDS`。  
   若不需要通知，可将 `ENABLE_WXPUSHER` 设为 `false`。

3. **配置 GitHub 自动推送（可选）**  
   根据你的操作系统，编辑对应的推送脚本：
   - **Windows**：编辑 `git_sync.ps1`
   - **Linux**：编辑 `git_sync.sh`
   
   修改以下四项为你的真实信息：
   ```text
   github_token="你的 GitHub Personal Access Token"
   github_username="你的 GitHub 用户名"
   repo_name="仓库名"
   branch="分支名"
   ```
   若不需要推送到 GitHub，可在 `config.json` 中将 `GITHUB_SYNC_MAX_RETRIES` 设为 `0` 并手动注释 `main.py` 末尾的 `sync_to_github()` 调用（通常无需修改）。

4. **配置 Cloudflare DNS 自动更新（可选）**  
   如需将优选 IP 自动更新到 Cloudflare DNS，请参考下方 [Cloudflare DNS 批量更新参数](#cloudflare-dns-批量更新参数) 获取 API 令牌及 Zone ID，并填写 `config.json` 中 `CF_` 开头的相关配置项。

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
| **进入项目目录** | `cd "C:\Users\你的用户名\Desktop\cfnb"` |
| **解除执行限制（如需要）** | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| **运行部署脚本** | `.\setup.ps1` |
| **编辑推送脚本** | 编辑 `git_sync.ps1`，填入你的 GitHub 令牌等信息 |
| **测试运行** | `python main.py` |

脚本自动完成：安装 Python/Git/curl、requests 库、创建 .gitignore、配置计划任务（下个整 15 分开始，无限期重复）。

### Linux 部署

| 步骤 | 操作 |
| :--- | :--- |
| **进入项目目录** | `cd /path/to/cfnb` |
| **赋予执行权限** | `chmod +x setup.sh` |
| **运行部署脚本** | `sudo ./setup.sh` |
| **编辑推送脚本** | 编辑 `git_sync.sh`，填入你的 GitHub 令牌等信息 |
| **测试运行** | `python3 main.py` |

脚本自动完成：检测包管理器安装 Python3/pip/Git/curl、requests 库、创建 .gitignore、配置 cron 定时任务（整点 15 分对齐）。

<details>
<summary>📝 手动部署详细步骤（点击展开）</summary>

#### Windows 手动部署

1. 安装 [Python 3](https://www.python.org/downloads/)（安装时务必勾选 “Add Python to PATH”）。
2. 安装 [Git](https://git-scm.com/download/win)（默认选项即可）。
3. 安装 [curl](https://curl.se/windows/)（选择适合你系统的版本，并将 curl.exe 所在目录添加到系统 PATH 环境变量）。
4. 在项目目录地址栏输入 `cmd` 并回车，打开命令提示符，执行以下命令安装 Python 依赖：
   ```cmd
   pip install requests
   ```
5. （可选）手动创建计划任务：
   - 按 `Win + R`，输入 `taskschd.msc` 打开任务计划程序。
   - 点击右侧“创建任务”，按 `setup.ps1` 中的配置填写：
     - 常规：名称 `Cloudflare IP 优选`，勾选“不管用户是否登录都要运行”和“使用最高权限运行”。
     - 触发器：新建 → 开始任务“按预定计划” → 设置“一次”，开始时间为下一个整15分钟时刻；高级设置中勾选“重复任务间隔”，选择“15分钟”，持续时间“无限期”。
     - 操作：新建 → 操作“启动程序”，程序或脚本填写 `python.exe` 的完整路径，添加参数填写 `main.py` 的完整路径，起始于填写项目目录。
   - 点击确定，输入 Windows 登录密码保存。

#### Linux 手动部署

1. 安装系统依赖（以 Debian/Ubuntu 为例）：
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip git curl
   ```
   其他发行版请使用对应的包管理器（yum/dnf/pacman）安装同名软件包。

2. 安装 Python 依赖：
   ```bash
   pip3 install requests
   ```

3. 赋予推送脚本执行权限（如果需要 GitHub 自动同步）：
   ```bash
   chmod +x git_sync.sh
   ```

4. （可选）手动添加 cron 定时任务：
   ```bash
   (crontab -l 2>/dev/null; echo "0,15,30,45 * * * * cd $(pwd) && /usr/bin/python3 $(pwd)/main.py >> $(pwd)/cron.log 2>&1") | crontab -
   ```
   如需修改运行频率，调整分钟字段即可（例如 `*/10` 表示每 10 分钟）。

5. 验证 cron 任务是否添加成功：
   ```bash
   crontab -l
   ```

</details>

---

## 🕒 定时自动运行说明

| 平台 | 方式 | 行为 |
| :--- | :--- | :--- |
| Windows | 计划任务 `Cloudflare IP 优选` | 从下一个整 15 分钟开始（如 17:47 → 18:00），之后每 15 分钟**永久重复**，不因跨天重置 |
| Linux | cron 定时任务 | 分钟字段为 `0,15,30,45`，每小时的整 15 分钟运行一次 |

**日志查看**：
- Windows：可在任务计划程序中查看历史运行状态。
- Linux：日志输出至项目目录下的 `cron.log`，使用 `tail -f cron.log` 实时查看。

---

## ⚙️ 配置说明（完整参数详解）

> [!NOTE]
> **运行环境说明**  
> 本工具默认参数基于 **2核2G 云服务器** 环境稳定测试通过。  
> 若您在 **软路由（如 OpenWrt）、树莓派或低配置 PC** 上运行，建议适当降低并发参数（如 `MAX_WORKERS`、`BANDWIDTH_WORKERS`），避免因资源不足导致测试超时或系统卡顿。具体调优建议请参考下文各参数的详细说明。

所有运行参数均集中在 `config.json` 文件中。以下为 **每一个配置项** 的详细说明，您可根据自身网络环境和需求进行调整。

### 筛选模式与数量控制

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `USE_GLOBAL_MODE` | `boolean` | `true` | **筛选模式**。<br>`true` = 全局优选模式（从所有节点中选出最优的 `GLOBAL_TOP_N` 个）。<br>`false` = 分国家优选模式（每个国家选出最优的 `PER_COUNTRY_TOP_N` 个）。 |
| `GLOBAL_TOP_N` | `int` | `16` | 全局模式下最终保留的节点数量（仅在 `USE_GLOBAL_MODE=true` 时生效）。 |
| `PER_COUNTRY_TOP_N` | `int` | `1` | 分国家模式下每个国家保留的节点数量（仅在 `USE_GLOBAL_MODE=false` 时生效）。 |
| `BANDWIDTH_CANDIDATES` | `int` | `80` | **候选池大小**：从 TCP 测试通过者中选取前 N 个节点进入后续的可用性检测和带宽测速。增大该值可让更多节点参与最终竞争，但会延长总运行时间。 |

### TCP 连接测试参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `TCP_PROBES` | `int` | `7` | 每个节点测试 TCP 连接的次数。增加次数可提高延迟数据的准确性，但会增加总测试时间。 |
| `MIN_SUCCESS_RATE` | `float` | `1.0` | **最低成功率阈值**（0.0 ~ 1.0）。节点在 `TCP_PROBES` 次测试中的成功比例必须 ≥ 此值才能进入下一轮。`1.0` 表示要求全部连接成功。若网络波动大，可适当降低（如 `0.7`）。 |
| `TIMEOUT` | `float` | `2.5` | 单次 TCP 连接超时时间（秒）。超时未连上的即判定失败。网络延迟较高时可酌情增加。 |

### 节点数据源与输出

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `JSON_URL` | `string` | `"https://zip.cm.edu.kg/all.txt"` | Cloudflare IP 节点数据源 URL（TXT 格式，每行 `IP:端口#国家`）。可替换为其他兼容源。 |
| `OUTPUT_FILE` | `string` | `"ip.txt"` | 最终优选节点保存的文件名。程序运行后会覆盖写入该文件。 |

### 国家过滤参数（前置优化）

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `FILTER_COUNTRIES_ENABLED` | `boolean` | `false` | 是否启用国家过滤。若为 `true`，则只保留 `ALLOWED_COUNTRIES` 中列出的国家/地区的节点。**过滤在 TCP 测试前执行，可大幅减少测试量。** |
| `ALLOWED_COUNTRIES` | `array` | `[]` | 允许的国家代码列表（如 `["HK","US","JP"]`），仅在 `FILTER_COUNTRIES_ENABLED=true` 时生效。国家代码应为两位大写字母。 |

### 微信通知（WxPusher）参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `ENABLE_WXPUSHER` | `boolean` | `true` | 是否启用 WxPusher 微信通知。 |
| `WXPUSHER_APP_TOKEN` | `string` | `""` | **【必填】** WxPusher 的 APP_TOKEN。请从 [WxPusher 管理后台](https://wxpusher.zjiecode.com/admin/) 获取。 |
| `WXPUSHER_UIDS` | `array` | `[""]` | **【必填】** 接收通知的用户 UID 列表。请从 WxPusher 获取您的 UID 并填入。 |
| `WXPUSHER_API_URL` | `string` | `"http://wxpusher.zjiecode.com/api/send/message"` | 消息发送 API 地址，一般无需修改。 |

> 💡 若不需要通知，将 `ENABLE_WXPUSHER` 设为 `false` 即可。

### Cloudflare DNS 批量更新参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `CF_ENABLED` | `boolean` | `false` | 是否启用 Cloudflare DNS 自动批量更新。 |
| `CF_API_TOKEN` | `string` | `""` | Cloudflare API 令牌（需具有 Zone:DNS:Edit 权限）。 |
| `CF_ZONE_ID` | `string` | `""` | 域名区域 ID，在 Cloudflare 域名概览页右侧可找到。 |
| `CF_DNS_RECORD_NAME` | `string` | `""` | 要更新的完整子域名，例如 `cf-proxy.yourdomain.com`。 |
| `CF_TTL` | `int` | `60` | DNS 记录的 TTL（秒）。<br>可设置为 `1` 表示“自动”（实际为 300 秒）；其他常见值为 `60`、`120`、`300` 等。<br>**注意**：仅当 `CF_PROXIED = false`（仅 DNS 模式）时自定义 TTL 才生效；若开启代理，TTL 将被强制设为自动。 |
| `CF_PROXIED` | `boolean` | `false` | 是否启用 Cloudflare CDN 代理（橙色云朵）。通常设为 `false`（仅 DNS 解析）。 |

<details>
<summary>🔧 点击展开高级参数（可用性检测 / 带宽测速 / 纯净度 / 并发 / 重试）</summary>

### 可用性检测参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `TEST_AVAILABILITY` | `boolean` | `true` | 是否对候选节点进行 **可用性二次筛选**（调用专用 API 检测节点能否正常代理请求）。推荐保持开启。 |
| `FILTER_IPV6_AVAILABILITY` | `boolean` | `true` | **（新版语义）** 是否在 **Cloudflare DNS 更新时** 过滤掉落地 IP 为 IPv6 的节点。设为 `true` 后，DNS 记录只会包含落地 IPv4 的节点，**但不会影响 `ip.txt` 的输出和带宽测速候选池**。 |
| `AVAILABILITY_CHECK_API` | `string` | `"https://check-proxyip-api.cmliussss.net/check"` | 可用性检测 API 地址。一般无需修改，除非服务地址变更。 |
| `AVAILABILITY_TIMEOUT` | `float` | `8.0` | 单次 API 请求的超时时间（秒）。 |
| `AVAILABILITY_RETRY_MAX` | `int` | `2` | 可用性检测整体失败（通过率为0）时的最大重试轮数。 |
| `AVAILABILITY_RETRY_DELAY` | `int` | `5` | 可用性检测重试间隔（秒）。 |

### 带宽测速参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `BANDWIDTH_SIZE_MB` | `int` | `1` | 测速下载文件大小（MB）。值越大测速越精准，但耗时越长。建议保持 1-5 MB。 |
| `BANDWIDTH_TIMEOUT` | `float` | `5.0` | 单个节点的带宽测速超时时间（秒）。如果文件在规定时间内无法下载完成，则判定测速失败。 |
| `BANDWIDTH_RETRY_MAX` | `int` | `2` | **带宽测速整体重试次数**。当一轮测速后**所有候选节点均失败**（无任何有效速度）时，程序将等待 `BANDWIDTH_RETRY_DELAY` 秒后重新执行测速，最多重复 `BANDWIDTH_RETRY_MAX` 轮。若全部轮次仍无结果，则发送微信通知并降级使用 TCP 排序节点。 |
| `BANDWIDTH_RETRY_DELAY` | `int` | `5` | 带宽测速整体重试前的等待时间（秒）。 |
| `BANDWIDTH_URL_TEMPLATE` | `string` | `"https://speed.cloudflare.com/__down?bytes={bytes}"` | 带宽测速 URL 模板，`{bytes}` 会被替换为 `BANDWIDTH_SIZE_MB * 1024 * 1024`。一般无需修改。 |

### 纯净度检测参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `ENABLE_IP_PURITY_CHECK` | `boolean` | `true` | 是否在带宽测速后对节点进行 **IP 纯净度检测**。要求 `company.abuser_score` 和 `asn.abuser_score` 均为 `Low`。 |
| `IP_PURITY_API` | `string` | `"https://api.ipapi.is/"` | 纯净度检测 API 地址。 |
| `IP_PURITY_WORKERS` | `int` | `10` | 纯净度检测的并发线程数。 |
| `IP_PURITY_TIMEOUT` | `int` | `8` | 纯净度 API 请求超时（秒）。 |
| `IP_PURITY_RETRY_MAX` | `int` | `2` | 纯净度检测整体失败时的最大重试轮数。 |
| `IP_PURITY_RETRY_DELAY` | `int` | `5` | 纯净度检测重试间隔（秒）。 |
| `IP_PURITY_FALLBACK` | `boolean` | `true` | 多次重试仍全部失败时是否降级使用原带宽测速结果。 |

### 并发控制参数

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `MAX_WORKERS` | `int` | `150` | TCP 并发测试的最大线程数。值越高测试越快，但会占用更多系统资源。若运行时出现大量超时错误，可适当降低。 |
| `AVAILABILITY_WORKERS` | `int` | `20` | 可用性检测的并发线程数。 |
| `BANDWIDTH_WORKERS` | `int` | `6` | 带宽测速的并发线程数。**注意**：测速非常消耗带宽，并发过高可能导致测速结果不准确或网络拥堵，建议不超过 10。 |

### 重试策略配置

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `DNS_UPDATE_MAX_RETRIES` | `int` | `5` | DNS 更新失败时的最大重试次数。 |
| `DNS_UPDATE_RETRY_DELAY` | `int` | `10` | DNS 更新重试间隔（秒）。 |
| `GITHUB_SYNC_MAX_RETRIES` | `int` | `5` | GitHub 推送失败时的最大重试次数。 |
| `GITHUB_SYNC_RETRY_DELAY` | `int` | `10` | GitHub 推送重试间隔（秒）。 |

</details>

> 💡 **配置建议**：  
> - 对于大多数用户，仅需修改 `ALLOWED_COUNTRIES`、`WXPUSHER_APP_TOKEN` 和 `WXPUSHER_UIDS` 即可满足需求。  
> - 如需启用 DNS 更新，请仔细阅读下方“Cloudflare DNS 批量更新说明”并正确填写 `CF_*` 参数。  
> - 若网络环境较差，可适当增加 `TCP_PROBES` 和 `TIMEOUT`，并降低 `MIN_SUCCESS_RATE` 和 `MAX_WORKERS`。  
> - 若希望更快获得结果，可减少 `BANDWIDTH_CANDIDATES` 或 `BANDWIDTH_SIZE_MB`。

---

## ☁️ Cloudflare DNS 批量更新说明

本工具支持将优选出的 IP 地址列表，以 **多 IP 轮询（Round-Robin）** 的方式自动更新到 Cloudflare DNS。每次运行时，脚本会：

1. 查询目标子域名（例如 `cf-proxy.yourdomain.com`）下现有的所有 A 记录。
2. **（新版优化）** 若启用了 `FILTER_IPV6_AVAILABILITY`，程序将从 **全部参与带宽测速的候选节点** 中，按测速结果从快到慢依次挑选落地 IPv4 的节点，最多选取 `GLOBAL_TOP_N`（或 `PER_COUNTRY_TOP_N`）个。这样可以充分利用候选池，避免因 `ip.txt` 中混有 IPv6 落地节点而导致 DNS 记录数量不足。
3. 利用 Cloudflare 批量 API，**先删除所有旧记录，再为筛选出的节点创建同名 A 记录**。
4. 整个过程在一个原子操作中完成，确保最终 DNS 记录与优选策略一致。

**使用前提**：
- 拥有 Cloudflare 账号，并将域名托管在 Cloudflare。
- 创建具有 `Zone:DNS:Edit` 权限的 **API Token**（获取方法：Cloudflare 仪表盘 → 我的个人资料 → API 令牌 → 创建令牌 → 使用“编辑区域 DNS”模板）。
- 获取域名的 **Zone ID**（在域名概览页面右侧可找到）。

**注意事项**：
- 免费套餐单次批量操作最多支持 200 条记录，通常足够使用。
- 若候选池中落地 IPv4 节点总数不足目标数量，则更新实际可用的数量，不会强制凑满。
- 全量替换策略在极短时间窗口内可能导致解析短暂为空，但对绝大多数应用场景无影响。
- 如需完全避免服务中断，可自行修改代码为增量更新（只增删差异部分）。

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

## 🚀 对接 EdgeTunnel (2.0+) 指南

**EdgeTunnel** (EDTunnel) 是基于 Cloudflare Workers 的隧道工具。使用本项目筛选出的 `ip.txt` 可以显著提升连接速度和稳定性。

### 方法一：优选订阅模式（推荐）

1. 复制你的 GitHub Raw 链接：
   `https://raw.githubusercontent.com/你的用户名/仓库名/refs/heads/分支名/ip.txt`
2. 打开 EdgeTunnel 控制面板，进入 **“优选订阅模式”**。
3. 在 **“自定义订阅”** 处填入上述 GitHub Raw 链接。
4. 保存配置，程序将根据你筛选出的最优 IP 自动构建隧道节点。

### 方法二：手动替换 EdgeTunnel 节点配置

1. 打开 `ip.txt`，从列表中选择排在正序（带宽最高）的 **IP 地址** 和 **端口**。
2. 打开 EdgeTunnel 控制面板，进入 **“优选订阅模式”**。
3. 在 **“自定义订阅”** 处填入上述 **IP 地址** 和 **端口**。
4. 保存配置。

### 方法三：使用 Cloudflare DNS 域名（最新功能）

如果您已启用 Cloudflare DNS 批量更新，则可以直接在 EdgeTunnel 的“自定义订阅”或“PROXYIP”处填入您配置的子域名（如 `cf-proxy.yourdomain.com`）。该域名会自动解析到当前最优的多个 IP 之一，实现零配置动态切换。

### 💡 为什么这样对接更有效？
- **低延迟**：`main.py` 已经通过 TCP 握手筛选出了延迟最低的节点。
- **高带宽**：结果经过真实 `curl` 下载测试，排在前面的节点具有更强的并发吞吐能力。
- **高可用**：通过 `AVAILABILITY_CHECK_API` 过滤了那些能 Ping 通但无法正常通过代理请求的无效 IP。
- **高纯净度**：通过 `ipapi.is` 排除了被标记为滥用的 IP，降低被目标网站屏蔽的风险。
- **自动更新**：DNS 记录随优选结果自动刷新，无需手动修改配置。

---

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

6. **Linux 下 `git_sync.sh` 权限被拒绝**  
   执行 `chmod +x git_sync.sh` 赋予执行权限。

</details>

<details>
<summary>📤 GitHub 推送与同步</summary>

4. **GitHub 推送失败**  
   - 检查 `git_sync.ps1` / `git_sync.sh` 中的 Token、用户名、仓库名是否正确。
   - 确保 Token 具备 `repo` 权限。
   - 确认本地 Git 已正确配置用户信息（`git config --global user.name/email`）。

9. **GitHub 推送时提示权限错误或 403**  
   - 请确认令牌具有 `repo` 权限，且未过期。创建令牌时务必勾选 **repo** 全部子项，并将过期时间设为 **No expiration**。

</details>

<details>
<summary>☁️ Cloudflare DNS 更新</summary>

5. **Cloudflare DNS 更新失败**  
   - 检查 `CF_API_TOKEN` 是否有效且具有 Zone:DNS:Edit 权限。
   - 检查 `CF_ZONE_ID` 是否正确。
   - 检查 `CF_DNS_RECORD_NAME` 是否为完整的子域名且已托管在 Cloudflare。
   - 脚本自带 5 次重试机制，若全部失败会通过微信通知。

8. **为什么我的 DNS 记录数量少于 `GLOBAL_TOP_N`？**  
   如果您启用了 `FILTER_IPV6_AVAILABILITY`，且候选池中落地 IPv4 的节点总数不足目标数量，则 DNS 只会更新实际可用的节点数。这是正常现象，您可以通过增加 `BANDWIDTH_CANDIDATES` 来扩大候选池。

</details>

<details>
<summary>🔍 检测与过滤</summary>

3. **可用性检测或纯净度检测全部失败**  
   若 API 接口异常，程序会自动跳过此步骤并回退到 TCP 筛选结果，同时发送微信提醒（如已配置）。纯净度检测还可通过 `IP_PURITY_FALLBACK` 控制是否降级。

</details>

<details>
<summary>🔒 隐私与其他</summary>

7. **隐私保护**  
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
