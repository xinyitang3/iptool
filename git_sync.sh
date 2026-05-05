#!/bin/bash
# git_sync.sh
# 功能：将当前目录下的 ip.txt 文件强制推送到 GitHub 仓库的 main 分支
# 使用场景：配合 Cloudflare IP 优选工具，自动同步优选结果到远程仓库
#
# ⚠️ 安全提醒：使用前请将下方的 github_token 替换为你自己的 GitHub Personal Access Token
#    切勿将真实令牌提交到公开仓库！

# ==================== GitHub 认证信息（从环境变量读取） ====================
# 个人访问令牌（Personal Access Token），用于身份验证
# 请在系统环境变量中设置：export GITHUB_TOKEN="your_token"
github_token="${GITHUB_TOKEN:-}"
# GitHub 用户名（从环境变量读取）
github_username="${GITHUB_USERNAME:-}"
# 仓库名称（从环境变量读取）
repo_name="${GITHUB_REPO:-}"
# 目标分支（从环境变量读取）
branch="${GITHUB_BRANCH:-main}"

# 检查必要的环境变量
if [ -z "$github_token" ] || [ -z "$github_username" ] || [ -z "$repo_name" ]; then
    echo "⚠️ 环境变量未设置，跳过 GitHub 同步。"
    echo "请设置环境变量："
    echo "  export GITHUB_TOKEN=\"your_token\""
    echo "  export GITHUB_USERNAME=\"your_username\""
    echo "  export GITHUB_REPO=\"your_repo_name\""
    exit 0
fi

# ==================== 切换到脚本所在目录 ====================
cd "$(dirname "$0")" || exit 1
echo "[git_sync] 工作目录: $(pwd)"

# ==================== 处理可能的冲突 ====================
echo "[git_sync] 正在同步远程最新代码..."
if git fetch origin "$branch" 2>&1; then
    LOCAL_COMMIT=$(git rev-parse HEAD 2>/dev/null)
    REMOTE_COMMIT=$(git rev-parse origin/$branch 2>/dev/null)

    if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
        echo "[git_sync] 检测到远程有更新，尝试合并..."
        # 暂存本地 ip.txt
        if [ -f ip.txt ]; then
            cp ip.txt /tmp/ip.txt.backup
            echo "[git_sync] 已备份本地 ip.txt"
        fi

        # 拉取远程（使用 rebase 避免冲突）
        if git pull origin "$branch" --rebase 2>&1; then
            # 恢复远程的 ip.txt（因为多设备场景下远程的 ip.txt 通常是最新扫描结果）
            if [ -f /tmp/ip.txt.backup ]; then
                mv /tmp/ip.txt.backup ip.txt
                echo "[git_sync] 已恢复 ip.txt"
            fi
            echo "[git_sync] 合并成功！"
        else
            # rebase 失败，强制重置到远程版本
            git reset --hard origin/$branch
            if [ -f /tmp/ip.txt.backup ]; then
                mv /tmp/ip.txt.backup ip.txt
            fi
            echo "[git_sync] 已重置到远程版本"
        fi
    fi
else
    echo "[git_sync] 获取远程信息失败，继续尝试..."
fi

# ==================== 暂存并提交 ip.txt ====================
echo "[git_sync] 正在提交 ip.txt..."
git add ip.txt
commit_msg="Update ip.txt on $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$commit_msg"

# ==================== 强制推送到 GitHub ====================
echo "[git_sync] 正在推送到 GitHub..."
echo "[git_sync] 仓库: https://github.com/${github_username}/${repo_name}.git"
echo "[git_sync] 分支: $branch"

if git push "https://${github_token}@github.com/${github_username}/${repo_name}.git" "$branch" --force 2>&1; then
    echo "[git_sync] ✅ 推送成功！"
else
    echo "[git_sync] ❌ 推送失败！"
    echo "[git_sync] 请检查："
    echo "[git_sync]   1. GITHUB_TOKEN 是否有效"
    echo "[git_sync]   2. 仓库访问权限是否正确"
    echo "[git_sync]   3. 网络连接是否正常"
    exit 1
fi