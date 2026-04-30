#!/bin/bash
# setup.sh - Cloudflare IP 优选工具 Linux 一键部署脚本
# 
# 用法：
#   chmod +x setup.sh
#   sudo ./setup.sh          # 推荐使用 sudo 以便安装软件包
#   或
#   ./setup.sh               # 若仅为当前用户配置定时任务，可不用 sudo

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

# ---------- 管理员权限检查与友好提示（对齐 Windows 版） ----------
check_root() {
    if [[ $EUID -eq 0 ]]; then
        return 0  # 已是 root
    else
        echo -e "${YELLOW}⚠️  当前未以 root 身份运行。${NC}"
        echo -e "本脚本安装系统软件包需要管理员权限，建议使用 sudo 运行。"
        echo -e "如果您仅需为当前用户配置定时任务，也可以继续（但可能无法自动安装缺失的软件）。"
        echo ""
        read -p "是否继续以非 root 身份运行？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${CYAN}请使用以下命令重新运行：${NC}"
            echo -e "  sudo ./setup.sh"
            echo ""
            exit 1
        fi
        return 1  # 非 root 但用户选择继续
    fi
}

check_root

# ---------- 1. 检测并安装系统依赖 ----------
echo -e "${GREEN}[1/4] 检查系统依赖...${NC}"

# 检测包管理器
if command_exists apt-get; then
    PKG_MANAGER="apt-get"
    INSTALL_CMD="sudo apt-get update; sudo apt-get install -y"
elif command_exists yum; then
    PKG_MANAGER="yum"
    INSTALL_CMD="sudo yum install -y"
elif command_exists dnf; then
    PKG_MANAGER="dnf"
    INSTALL_CMD="sudo dnf install -y"
elif command_exists pacman; then
    PKG_MANAGER="pacman"
    INSTALL_CMD="sudo pacman -S --noconfirm"
elif command_exists brew; then
    PKG_MANAGER="brew"
    INSTALL_CMD="brew install"
else
    echo -e "${RED}❌ 未检测到支持的包管理器。${NC}"
    echo -e "请手动安装以下软件：python3, pip, git, curl"
    echo -e "或者安装 Homebrew (macOS): /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo -e "然后重新运行本脚本。"
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
    eval "$INSTALL_CMD python3-pip"
    if ! command_exists pip3; then
        echo -e "${RED}❌ pip3 安装失败，请手动安装后重试。${NC}"
        exit 1
    fi
fi

# Git
if command_exists git; then
    echo -e "✅ Git 已安装: $(which git)"
else
    echo -e "${YELLOW}正在安装 Git...${NC}"
    eval "$INSTALL_CMD git"
    if ! command_exists git; then
        echo -e "${RED}❌ Git 安装失败，请手动安装后重试。${NC}"
        exit 1
    fi
fi

# curl
if command_exists curl; then
    echo -e "✅ curl 已安装: $(which curl)"
else
    echo -e "${YELLOW}正在安装 curl...${NC}"
    eval "$INSTALL_CMD curl"
    if ! command_exists curl; then
        echo -e "${RED}❌ curl 安装失败，请手动安装后重试。${NC}"
        exit 1
    fi
fi

echo ""

# ---------- 2. 创建 Python 虚拟环境（venv） ----------
echo -e "${GREEN}[2/4] 检查/创建 Python 虚拟环境...${NC}"
VENV_DIR="$SCRIPT_DIR/venv"

# 检查是否已存在虚拟环境
if [ -d "$VENV_DIR" ]; then
    echo -e "✅ 虚拟环境已存在: $VENV_DIR"
else
    echo -e "${YELLOW}正在创建虚拟环境...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ -d "$VENV_DIR" ]; then
        echo -e "${GREEN}✅ 虚拟环境创建成功。${NC}"
    else
        echo -e "${RED}❌ 虚拟环境创建失败，请手动创建: python3 -m venv venv${NC}"
        exit 1
    fi
fi

# 激活虚拟环境并设置路径
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS/Linux
    source "$VENV_DIR/bin/activate"
    VENV_PYTHON="$VENV_DIR/bin/python"
    VENV_PIP="$VENV_DIR/bin/pip"
else
    # Windows（虽然脚本主要用于 Unix-like 系统）
    source "$VENV_DIR/Scripts/activate"
    VENV_PYTHON="$VENV_DIR/Scripts/python"
    VENV_PIP="$VENV_DIR/Scripts/pip"
fi
echo ""

# ---------- 3. 安装 Python 依赖 requests（智能跳过） ----------
echo -e "${GREEN}[3/4] 检查 Python 包 requests...${NC}"
if "$VENV_PIP" show requests &> /dev/null; then
    echo -e "✅ requests 已安装，跳过。"
else
    echo -e "${YELLOW}正在安装 requests...${NC}"
    "$VENV_PIP" install --upgrade pip --quiet
    "$VENV_PIP" install requests --quiet
    if "$VENV_PIP" show requests &> /dev/null; then
        echo -e "${GREEN}✅ requests 库安装完成。${NC}"
    else
        echo -e "${RED}❌ requests 安装失败，请手动执行: $VENV_PIP install requests${NC}"
        exit 1
    fi
fi
echo ""

# ---------- 4. 创建 .gitignore 保护隐私 ----------
echo -e "${GREEN}[4/5] 创建 .gitignore...${NC}"
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

# ---------- 5. 配置 cron 定时任务（对齐 Windows 的下个整5分开始 + 每5分钟重复） ----------
echo -e "${GREEN}[5/5] 配置定时任务（每${TASK_INTERVAL_MINUTES}分钟运行一次）...${NC}"

# 计算下一个整 5 分钟时刻（用于显示）
calc_next_aligned() {
    local interval=$1
    local current_min=$(date +%M)
    local current_hour=$(date +%H)
    local next_min=$(( ((current_min / interval) + 1) * interval ))
    local next_hour=$current_hour
    if [ $next_min -ge 60 ]; then
        next_min=0
        next_hour=$(( (next_hour + 1) % 24 ))
    fi
    printf "%02d:%02d" $next_hour $next_min
}

NEXT_RUN=$(calc_next_aligned $TASK_INTERVAL_MINUTES)
echo -e "   首次运行将发生在: ${CYAN}$NEXT_RUN${NC}（之后每 ${TASK_INTERVAL_MINUTES} 分钟运行一次）"

# 构建 cron 表达式：分钟字段为 */5（每5分钟）
CRON_MINUTE_FIELD="*/5"
PYTHON_PATH="$VENV_PYTHON"

# 智能检测优先级前缀（对齐 Windows 的高优先级逻辑）
if [[ $EUID -eq 0 ]]; then
    NICE_PREFIX="nice -n -10"
    echo -e "   运行优先级: 高 (nice -n -10)"
else
    echo -e "${YELLOW}⚠️  非 root 用户，cron 任务将以默认优先级运行。${NC}"
    NICE_PREFIX=""
fi

CRON_CMD="$CRON_MINUTE_FIELD * * * * cd \"$SCRIPT_DIR\" && $NICE_PREFIX \"$PYTHON_PATH\" \"$SCRIPT_DIR/$PYTHON_SCRIPT\" >> \"$SCRIPT_DIR/cron.log\" 2>&1"
CRON_COMMENT="# Cloudflare IP 优选工具定时任务（每5分钟，整点对齐）"

# 检查是否已存在相同任务（基于脚本路径去重）
if crontab -l 2>/dev/null | grep -F "$SCRIPT_DIR/$PYTHON_SCRIPT" > /dev/null; then
    echo -e "${YELLOW}⚠️ 定时任务已存在，跳过添加。${NC}"
else
    # 添加新任务
    (crontab -l 2>/dev/null || true; echo "$CRON_COMMENT"; echo "$CRON_CMD") | crontab -
    echo -e "${GREEN}✅ 定时任务已添加（每${TASK_INTERVAL_MINUTES}分钟，从下一个整5分钟开始）${NC}"
fi

echo -e "   执行命令: $NICE_PREFIX $PYTHON_PATH $SCRIPT_DIR/$PYTHON_SCRIPT"
echo -e "   日志文件: $SCRIPT_DIR/cron.log"
echo ""

# ---------- 赋予 git_sync.sh 执行权限（如果存在） ----------
if [ -f "git_sync.sh" ]; then
    chmod +x git_sync.sh
    echo -e "✅ 已赋予 git_sync.sh 执行权限"
fi

# ---------- 后续指引 ----------
echo ""
echo -e "${CYAN}========================================"
echo -e " 🎉 部署完成！"
echo -e "========================================${NC}\n"
echo -e "${YELLOW}👉 接下来请完成以下手动配置步骤：${NC}"
echo -e "1. 编辑 config.json，填写 WxPusher 的 APP_TOKEN 和 UID（如需通知）"
echo -e "2. 编辑 git_sync.sh，填写你的 GitHub Token、用户名及仓库名"
echo -e "3. 手动运行一次测试: ${CYAN}python3 main.py${NC}"
echo -e "4. 查看定时任务日志: ${CYAN}tail -f cron.log${NC}"
echo -e "5. 管理定时任务: ${CYAN}crontab -e${NC}"
echo ""

# 询问是否立即运行
read -p "是否立即运行一次 main.py 进行测试？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${CYAN}正在运行 main.py ...${NC}"
    "$VENV_PYTHON" "$PYTHON_SCRIPT"
fi

exit 0