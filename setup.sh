#!/usr/bin/env bash
# setup.sh - Cloudflare IP 优选工具 Linux 一键部署脚本
# 
# 用法：
#   chmod +x setup.sh
#   ./setup.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================"
echo -e " Cloudflare IP 优选工具 - 部署脚本"
echo -e "========================================${NC}\n"

# 切换到脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
echo -e "工作目录: $SCRIPT_DIR\n"

# ==================== 配置 ====================
TASK_INTERVAL_MINUTES=5
PYTHON_SCRIPT="main.py"
# =============================================

# ---------- 辅助函数：检测命令是否存在 ----------
command_exists() {
    command -v "$1" &> /dev/null
}

# ---------- 权限检查 ----------
check_root() {
    if [[ $EUID -eq 0 ]]; then
        return 0  # 已是 root
    else
        echo -e "${YELLOW}⚠️  当前未以 root 身份运行。${NC}"
        echo -e "本脚本安装系统软件包需要管理员权限，建议使用 sudo 运行。"
        echo ""
        read -p "是否继续以非 root 身份运行？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${CYAN}请使用以下命令重新运行：${NC}"
            echo -e "  sudo bash ./setup.sh"
            echo ""
            exit 1
        fi
        return 1
    fi
}

check_root

# 动态配置 sudo 前缀（如果是 root 则不用 sudo）
SUDO_CMD=""
if [[ $EUID -ne 0 ]]; then
    SUDO_CMD="sudo "
fi

# ---------- 1. 检测并安装系统依赖 ----------
echo -e "${GREEN}[1/4] 检查系统依赖...${NC}"

# 检测包管理器
if command_exists apk; then
    PKG_MANAGER="apk"
    INSTALL_CMD="${SUDO_CMD}apk add --no-cache"
elif command_exists apt-get; then
    PKG_MANAGER="apt-get"
    INSTALL_CMD="${SUDO_CMD}apt-get update && ${SUDO_CMD}apt-get install -y"
elif command_exists yum; then
    PKG_MANAGER="yum"
    INSTALL_CMD="${SUDO_CMD}yum install -y"
elif command_exists dnf; then
    PKG_MANAGER="dnf"
    INSTALL_CMD="${SUDO_CMD}dnf install -y"
elif command_exists pacman; then
    PKG_MANAGER="pacman"
    INSTALL_CMD="${SUDO_CMD}pacman -S --noconfirm"
elif command_exists brew; then
    PKG_MANAGER="brew"
    INSTALL_CMD="brew install"
else
    echo -e "${RED}❌ 未检测到支持的包管理器。${NC}"
    echo -e "请手动安装以下软件：python3, pip, git, curl"
    exit 1
fi

# Python3
if command_exists python3; then
    echo -e "✅ Python3 已安装: $(which python3)"
else
    echo -e "${YELLOW}正在安装 Python3...${NC}"
    eval "$INSTALL_CMD python3"
    if ! command_exists python3; then
        echo -e "${RED}❌ Python3 安装失败，请手动安装后重试。${NC}"
        exit 1
    fi
fi

# pip3
if command_exists pip3; then
    echo -e "✅ pip3 已安装: $(which pip3)"
else
    echo -e "${YELLOW}正在安装 pip3...${NC}"
    if [ "$PKG_MANAGER" == "apk" ]; then
        eval "$INSTALL_CMD py3-pip"
    elif [ "$PKG_MANAGER" == "pacman" ]; then
        eval "$INSTALL_CMD python-pip"
    else
        eval "$INSTALL_CMD python3-pip"
    fi
    
    if ! command_exists pip3; then
        echo -e "${RED}❌ pip3 安装失败，请手动安装后重试。${NC}"
        exit 1
    fi
fi

# Git 与 curl
for cmd in git curl; do
    if command_exists $cmd; then
        echo -e "✅ $cmd 已安装: $(which $cmd)"
    else
        echo -e "${YELLOW}正在安装 $cmd...${NC}"
        eval "$INSTALL_CMD $cmd"
    fi
done
echo ""

# ---------- 2 & 3. 准备 Python 环境并安装 requests ----------
echo -e "${GREEN}[2/4] 检查 Python 运行环境与依赖包...${NC}"

if [ "$PKG_MANAGER" == "apk" ]; then
    # 针对 Alpine/iSH 的专门优化：跳过慢速的 venv，直接使用系统包管理秒装 requests
    echo -e "${YELLOW}检测到 Alpine 模拟环境，跳过虚拟环境创建环节以避免卡死...${NC}"
    # 检查是否已安装 requests
    if python3 -c "import requests" 2>/dev/null; then
        echo -e "✅ requests 已安装，跳过。"
    else
        eval "$INSTALL_CMD py3-requests"
        echo -e "✅ requests 已通过原生包管理器安装完毕。"
    fi
    VENV_PYTHON="python3"
else
    # 正常 Linux 系统的 venv 逻辑
    VENV_DIR="$SCRIPT_DIR/venv"
    if [ -d "$VENV_DIR" ]; then
        echo -e "✅ 虚拟环境已存在: $VENV_DIR"
    else
        echo -e "${YELLOW}正在创建虚拟环境...${NC}"
        python3 -m venv "$VENV_DIR"
        if [ ! -d "$VENV_DIR" ]; then
            echo -e "${RED}❌ 虚拟环境创建失败。${NC}"
            exit 1
        fi
    fi
    source "$VENV_DIR/bin/activate"
    VENV_PYTHON="$VENV_DIR/bin/python"
    VENV_PIP="$VENV_DIR/bin/pip"
    
    if "$VENV_PIP" show requests &> /dev/null; then
        echo -e "✅ requests 已安装，跳过。"
    else
        echo -e "${YELLOW}正在使用 pip 安装 requests...${NC}"
        "$VENV_PIP" install --upgrade pip --quiet
        "$VENV_PIP" install requests --quiet
    fi
fi
echo ""

# ---------- 4. 创建 .gitignore ----------
echo -e "${GREEN}[3/4] 创建 .gitignore...${NC}"
cat > .gitignore << 'EOF'
config.json
git_sync.ps1
git_sync.sh
__pycache__/
venv/
EOF
echo -e "✅ .gitignore 已创建\n"

# ---------- 验证 main.py 是否存在 ----------
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}❌ 错误：未找到 $PYTHON_SCRIPT 文件，请确保脚本位于正确目录。${NC}"
    exit 1
fi

# ---------- 5. 配置 cron 定时任务 ----------
echo -e "${GREEN}[4/4] 配置定时任务（每${TASK_INTERVAL_MINUTES}分钟运行一次）...${NC}"

CRON_MINUTE_FIELD="*/5"
PYTHON_PATH="$VENV_PYTHON"

if [[ $EUID -eq 0 ]]; then
    NICE_PREFIX="nice -n -10"
    echo -e "   运行优先级: 高 (nice -n -10)"
else
    echo -e "${YELLOW}⚠️  非 root 用户，cron 任务将以默认优先级运行。${NC}"
    NICE_PREFIX=""
fi

CRON_CMD="$CRON_MINUTE_FIELD * * * * cd \"$SCRIPT_DIR\" && $NICE_PREFIX \"$PYTHON_PATH\" \"$SCRIPT_DIR/$PYTHON_SCRIPT\" >> \"$SCRIPT_DIR/cron.log\" 2>&1"
CRON_COMMENT="# Cloudflare IP 优选工具定时任务（每5分钟，整点对齐）"

if crontab -l 2>/dev/null | grep -F "$SCRIPT_DIR/$PYTHON_SCRIPT" > /dev/null; then
    echo -e "${YELLOW}⚠️ 定时任务已存在，跳过添加。${NC}"
else
    # 兼容缺少 crontab 的情况
    if command_exists crontab; then
        (crontab -l 2>/dev/null || true; echo "$CRON_COMMENT"; echo "$CRON_CMD") | crontab -
        echo -e "${GREEN}✅ 定时任务已添加${NC}"
    else
        echo -e "${RED}❌ 未找到 crontab 命令，无法自动添加定时任务。你可能需要运行 apk add dcron 来安装。${NC}"
    fi
fi

echo -e "   执行命令: $NICE_PREFIX $PYTHON_PATH $SCRIPT_DIR/$PYTHON_SCRIPT"
echo -e "   日志文件: $SCRIPT_DIR/cron.log"
echo ""

if [ -f "git_sync.sh" ]; then
    chmod +x git_sync.sh
fi

echo -e "${CYAN}========================================"
echo -e " 🎉 部署完成！"
echo -e "========================================${NC}\n"

read -p "是否立即运行一次 main.py 进行测试？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${CYAN}正在运行 main.py ...${NC}"
    $VENV_PYTHON "$PYTHON_SCRIPT"
fi

exit 0
