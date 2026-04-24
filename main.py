#!/usr/bin/env python3
"""
Cloudflare IP 优选工具 (TCP筛选 + IP可用性二次筛选 + curl带宽测速 + WxPusher通知)
依赖：requests, curl (系统自带)
配置文件：同目录下的 config.json（请根据需要修改参数）
结果保存到 ip.txt，并自动推送到 GitHub，同时批量更新到 Cloudflare DNS
支持 Windows / Linux
优化：国家过滤前置，减少无效 TCP 测试；重试参数可配置；所有网络请求连接超时分离
"""

import requests
import socket
import time
import sys
import re
import os
import subprocess
import shutil
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== 预编译正则 ====================
NODE_LINE_PATTERN = re.compile(r"^\d+\.\d+\.\d+\.\d+:\d+#[A-Z]{2}$")
NODE_PATTERN = re.compile(r"^(\d+\.\d+\.\d+\.\d+):(\d+)#(.+)$")
IP_PORT_PATTERN = re.compile(r"^(\d+\.\d+\.\d+\.\d+):(\d+)#")

# ==================== 加载配置文件 ====================
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    """加载 config.json 配置文件，缺失必填字段时抛出异常"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ 错误：未找到配置文件 {CONFIG_FILE}")
        print("请在同目录下创建 config.json 文件，内容参考示例。")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ 错误：配置文件格式不正确 - {e}")
        sys.exit(1)

    defaults = {
        "USE_GLOBAL_MODE": True,
        "GLOBAL_TOP_N": 15,
        "PER_COUNTRY_TOP_N": 1,
        "BANDWIDTH_CANDIDATES": 90,
        "TCP_PROBES": 3,
        "MIN_SUCCESS_RATE": 1.0,
        "TIMEOUT": 2.0,
        "SOCKET_DEFAULT_TIMEOUT": 3,
        "PROGRESS_PRINT_INTERVAL": 1,
        "FILTER_COUNTRIES_ENABLED": False,
        "ALLOWED_COUNTRIES": ["US"],
        "ENABLE_WXPUSHER": True,
        "WXPUSHER_APP_TOKEN": "your_app_token_here",
        "WXPUSHER_UIDS": ["your_uid_here"],
        "WXPUSHER_API_URL": "http://wxpusher.zjiecode.com/api/send/message",
        "NOTIFY_TIMEOUT": 3,
        "NOTIFY_CONNECT_TIMEOUT": 3,
        "CF_ENABLED": True,
        "CF_API_TOKEN": "your_CF_API_TOKEN",
        "CF_ZONE_ID": "your_CF_ZONE_ID",
        "CF_DNS_RECORD_NAME": "your_CF_DNS_RECORD_NAME",
        "CF_TTL": 60,
        "CF_PROXIED": False,
        "CF_DNS_CONNECT_TIMEOUT": 3,
        "CF_DNS_READ_TIMEOUT": 3,
        "JSON_URL": "https://zip.cm.edu.kg/all.txt",
        "FETCH_MAX_RETRIES": 3,
        "FETCH_RETRY_DELAY": 3,
        "FETCH_TIMEOUT": 3,
        "FETCH_CONNECT_TIMEOUT": 3,
        "OUTPUT_FILE": "ip.txt",
        "TEST_AVAILABILITY": True,
        "AVAILABILITY_CHECK_API": "https://api.check.proxyip.cmliussss.net/check",
        "AVAILABILITY_TIMEOUT": 3,
        "AVAILABILITY_CONNECT_TIMEOUT": 3,
        "AVAILABILITY_RETRY_MAX": 2,
        "AVAILABILITY_RETRY_DELAY": 3,
        "FILTER_IPV6_AVAILABILITY": True,
        "FILTER_BLOCKED_COUNTRIES_ENABLED": True,
        "BLOCKED_COUNTRIES": [
            "BD", "BI", "BY", "CD", "CF", "CN", "CU", "DE", "ET", "HK",
            "IR", "KP", "LY", "MO", "NG", "NL", "PK", "RU", "SD", "SO",
            "SY", "TH", "TW", "UA", "VE", "VN", "YE", "ZW"
        ],
        "DNS_UPDATE_TARGET_COUNT": 15,
        "BANDWIDTH_SIZE_MB": 0.5,
        "BANDWIDTH_TIMEOUT": 3,
        "BANDWIDTH_RETRY_MAX": 2,
        "BANDWIDTH_RETRY_DELAY": 3,
        "BANDWIDTH_URL_TEMPLATE": "https://speed.cloudflare.com/__down?bytes={bytes}",
        "BANDWIDTH_PROCESS_BUFFER": 2,
        "BANDWIDTH_CONNECT_TIMEOUT": 3,
        "MAX_WORKERS": 200,
        "AVAILABILITY_WORKERS": 10,
        "BANDWIDTH_WORKERS": 10,
        "DNS_UPDATE_MAX_RETRIES": 3,
        "DNS_UPDATE_RETRY_DELAY": 3,
        "GITHUB_SYNC_MAX_RETRIES": 3,
        "GITHUB_SYNC_RETRY_DELAY": 3,
        "GIT_SYNC_PROCESS_TIMEOUT": 180,
    }

    for key, value in defaults.items():
        if key not in config:
            config[key] = value
            print(f"⚠️ 配置项 {key} 未设置，使用默认值：{value}")

    return config

cfg = load_config()

USE_GLOBAL_MODE = cfg["USE_GLOBAL_MODE"]
GLOBAL_TOP_N = cfg["GLOBAL_TOP_N"]
PER_COUNTRY_TOP_N = cfg["PER_COUNTRY_TOP_N"]
BANDWIDTH_CANDIDATES = cfg["BANDWIDTH_CANDIDATES"]
TCP_PROBES = cfg["TCP_PROBES"]
MIN_SUCCESS_RATE = cfg["MIN_SUCCESS_RATE"]
TIMEOUT = cfg["TIMEOUT"]
SOCKET_DEFAULT_TIMEOUT = cfg["SOCKET_DEFAULT_TIMEOUT"]
PROGRESS_PRINT_INTERVAL = cfg["PROGRESS_PRINT_INTERVAL"]
FILTER_COUNTRIES_ENABLED = cfg["FILTER_COUNTRIES_ENABLED"]
ALLOWED_COUNTRIES = cfg["ALLOWED_COUNTRIES"]
ENABLE_WXPUSHER = cfg["ENABLE_WXPUSHER"]
WXPUSHER_APP_TOKEN = cfg["WXPUSHER_APP_TOKEN"]
WXPUSHER_UIDS = cfg["WXPUSHER_UIDS"]
WXPUSHER_API_URL = cfg["WXPUSHER_API_URL"]
NOTIFY_TIMEOUT = cfg["NOTIFY_TIMEOUT"]
NOTIFY_CONNECT_TIMEOUT = cfg["NOTIFY_CONNECT_TIMEOUT"]
CF_ENABLED = cfg["CF_ENABLED"]
CF_API_TOKEN = cfg["CF_API_TOKEN"]
CF_ZONE_ID = cfg["CF_ZONE_ID"]
CF_DNS_RECORD_NAME = cfg["CF_DNS_RECORD_NAME"]
CF_TTL = cfg["CF_TTL"]
CF_PROXIED = cfg["CF_PROXIED"]
CF_DNS_CONNECT_TIMEOUT = cfg["CF_DNS_CONNECT_TIMEOUT"]
CF_DNS_READ_TIMEOUT = cfg["CF_DNS_READ_TIMEOUT"]
JSON_URL = cfg["JSON_URL"]
FETCH_MAX_RETRIES = cfg["FETCH_MAX_RETRIES"]
FETCH_RETRY_DELAY = cfg["FETCH_RETRY_DELAY"]
FETCH_TIMEOUT = cfg["FETCH_TIMEOUT"]
FETCH_CONNECT_TIMEOUT = cfg["FETCH_CONNECT_TIMEOUT"]
OUTPUT_FILE = cfg["OUTPUT_FILE"]
TEST_AVAILABILITY = cfg["TEST_AVAILABILITY"]
AVAILABILITY_CHECK_API = cfg["AVAILABILITY_CHECK_API"]
AVAILABILITY_TIMEOUT = cfg["AVAILABILITY_TIMEOUT"]
AVAILABILITY_CONNECT_TIMEOUT = cfg["AVAILABILITY_CONNECT_TIMEOUT"]
AVAILABILITY_RETRY_MAX = cfg["AVAILABILITY_RETRY_MAX"]
AVAILABILITY_RETRY_DELAY = cfg["AVAILABILITY_RETRY_DELAY"]
FILTER_IPV6_AVAILABILITY = cfg["FILTER_IPV6_AVAILABILITY"]
FILTER_BLOCKED_COUNTRIES_ENABLED = cfg["FILTER_BLOCKED_COUNTRIES_ENABLED"]
BLOCKED_COUNTRIES = cfg["BLOCKED_COUNTRIES"]
DNS_UPDATE_TARGET_COUNT = cfg["DNS_UPDATE_TARGET_COUNT"]
BANDWIDTH_SIZE_MB = cfg["BANDWIDTH_SIZE_MB"]
BANDWIDTH_TIMEOUT = cfg["BANDWIDTH_TIMEOUT"]
BANDWIDTH_RETRY_MAX = cfg["BANDWIDTH_RETRY_MAX"]
BANDWIDTH_RETRY_DELAY = cfg["BANDWIDTH_RETRY_DELAY"]
BANDWIDTH_URL_TEMPLATE = cfg["BANDWIDTH_URL_TEMPLATE"]
BANDWIDTH_PROCESS_BUFFER = cfg["BANDWIDTH_PROCESS_BUFFER"]
BANDWIDTH_CONNECT_TIMEOUT = cfg["BANDWIDTH_CONNECT_TIMEOUT"]
MAX_WORKERS = cfg["MAX_WORKERS"]
AVAILABILITY_WORKERS = cfg["AVAILABILITY_WORKERS"]
BANDWIDTH_WORKERS = cfg["BANDWIDTH_WORKERS"]
DNS_UPDATE_MAX_RETRIES = cfg["DNS_UPDATE_MAX_RETRIES"]
DNS_UPDATE_RETRY_DELAY = cfg["DNS_UPDATE_RETRY_DELAY"]
GITHUB_SYNC_MAX_RETRIES = cfg["GITHUB_SYNC_MAX_RETRIES"]
GITHUB_SYNC_RETRY_DELAY = cfg["GITHUB_SYNC_RETRY_DELAY"]
GIT_SYNC_PROCESS_TIMEOUT = cfg["GIT_SYNC_PROCESS_TIMEOUT"]

socket.setdefaulttimeout(SOCKET_DEFAULT_TIMEOUT)
BANDWIDTH_URL = BANDWIDTH_URL_TEMPLATE.format(bytes=int(BANDWIDTH_SIZE_MB * 1024 * 1024))

# ====================================================

def send_wxpusher_notification(content, summary):
    if not ENABLE_WXPUSHER:
        return
    try:
        payload = {
            "appToken": WXPUSHER_APP_TOKEN,
            "content": content,
            "summary": summary,
            "uids": WXPUSHER_UIDS
        }
        headers = {"Content-Type": "application/json; charset=utf-8"}
        resp = requests.post(
            WXPUSHER_API_URL,
            data=json.dumps(payload),
            headers=headers,
            timeout=(NOTIFY_CONNECT_TIMEOUT, NOTIFY_TIMEOUT)
        )
        if resp.status_code == 200:
            print("✅ 微信通知已发送")
        else:
            print(f"⚠️ 微信通知发送失败: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ 微信通知异常: {e}")

def fetch_nodes():
    """双模获取节点：支持云端下载与本地读取，用户手动选择"""
    print("\n" + "="*35)
    print(" 🚀 请选择本次测速的 IP 数据源：")
    print(" 1. 跑原项目云端库 (自动下载最新)")
    print(" 2. 跑本地私有库 (ipv4.txt 或 ipv4.csv)")
    print("="*35)
    
    try:
        choice = input("请输入数字 (1 或 2) 并按回车 (默认1): ").strip()
    except EOFError:
        # 防止在无交互环境(如 GitHub Actions)运行时卡死报错
        print("\n检测到非交互环境，默认选择 1 (云端)。")
        choice = "1"

    nodes = []
    if choice == "2":
        # ---------------- 模式 2：本地读取 ----------------
        target_file = "ipv4.txt"
        try:
            f = open(target_file, "r", encoding="utf-8", errors="ignore")
        except FileNotFoundError:
            target_file = "ipv4.csv"
            try:
                f = open(target_file, "r", encoding="utf-8", errors="ignore")
            except FileNotFoundError:
                print("❌ 错误：当前目录下找不到 ipv4.txt 或 ipv4.csv！")
                sys.exit(1)
        
        print(f"\n📂 正在读取本地 IP 库：{target_file} ...")
        with f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if re.match(r"^\d+\.\d+\.\d+\.\d+:\d+#[A-zA-Z]{2}$", line):
                    nodes.append(line)
                elif ',' in line:
                    ip = line.split(',')[0].strip()
                    if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip): nodes.append(f"{ip}:443#XX")
                elif re.match(r"^\d+\.\d+\.\d+\.\d+$", line):
                    nodes.append(f"{line}:443#XX")
        
        # 顺手做一下去重，保持顺序
        nodes = list(dict.fromkeys(nodes))
        print(f"✅ 成功从本地提取了 {len(nodes)} 个去重后的节点。")
        return nodes

    else:
        # ---------------- 模式 1：云端下载 ----------------
        # 修复了原代码中 config.get 变量名未定义的问题，改为 cfg.get
        json_url = cfg.get("JSON_URL", "https://zip.cm.edu.kg/all.txt")
            
        print(f"\n☁️ 正在请求云端源 {json_url} ...")
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.get(json_url, timeout=10)
                response.raise_for_status()
                for line in response.text.splitlines():
                    line = line.strip()
                    if line and re.match(r"^\d+\.\d+\.\d+\.\d+:\d+#[A-zA-Z]{2}$", line):
                        nodes.append(line)
                if nodes:
                    # 顺手去重
                    nodes = list(dict.fromkeys(nodes))
                    print(f"✅ 成功从云端解析 {len(nodes)} 个去重后的节点。")
                    return nodes
            except Exception as e:
                print(f"⚠️ 请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1: time.sleep(5)
        print("❌ 无法从远程获取节点，请检查网络！")
        sys.exit(1)


def test_tcp_latency(ip, port, timeout=TIMEOUT, probes=TCP_PROBES):
    min_latency = float("inf")
    success = 0
    for _ in range(probes):
        try:
            start = time.time()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((ip, int(port)))
            latency = time.time() - start
            if latency < min_latency:
                min_latency = latency
            success += 1
        except Exception:
            continue
    return min_latency, success

def test_node(node_str):
    m = NODE_PATTERN.match(node_str)
    if not m:
        return None
    ip, port, country = m.groups()
    min_lat, success = test_tcp_latency(ip, port)

    if success == 0 or (success / TCP_PROBES) < MIN_SUCCESS_RATE:
        return None

    return (node_str, min_lat, country, success)

def check_availability(node_str):
    m = IP_PORT_PATTERN.match(node_str)
    if not m:
        return (node_str, False, "unknown", {})
    ip, port = m.group(1), m.group(2)
    proxyip = f"{ip}:{port}"

    best_stack = "unknown"
    best_exit_info = {}
    success = False

    try:
        resp = requests.get(
            AVAILABILITY_CHECK_API,
            params={"proxyip": proxyip},
            timeout=(AVAILABILITY_CONNECT_TIMEOUT, AVAILABILITY_TIMEOUT)
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success") is True:
                success = True
                best_stack = data.get("inferred_stack", "unknown")
                probe = data.get("probe_results", {}).get("ipv6") or data.get("probe_results", {}).get("ipv4") or {}
                best_exit_info = probe.get("exit", {})
    except Exception:
        pass

    return (node_str, success, best_stack, best_exit_info)

def availability_filter_candidates(candidates):
    if not TEST_AVAILABILITY or not candidates:
        return candidates, {}, {}

    print(f"\n对 {len(candidates)} 个候选节点进行可用性二次筛选...")
    passed = []
    ip_info = {}
    exit_details = {}
    completed = 0
    total = len(candidates)
    last_print = time.time()

    with ThreadPoolExecutor(max_workers=AVAILABILITY_WORKERS) as executor:
        futures = {executor.submit(check_availability, node): node for node in candidates}
        for future in as_completed(futures):
            completed += 1
            node_str, ok, stack, exit_info = future.result()
            if ok:
                passed.append(node_str)
                ip_info[node_str] = stack
                exit_details[node_str] = exit_info
            now = time.time()
            if now - last_print >= PROGRESS_PRINT_INTERVAL or completed == total:
                print(f"\r[可用性检测] 进度：{completed}/{total} ({(completed/total)*100:.1f}%) 通过数量：{len(passed)}", end="", flush=True)
                last_print = now
    print()
    return passed, ip_info, exit_details

def availability_filter_with_retry(candidates):
    if not TEST_AVAILABILITY or not candidates:
        return candidates, {}, {}

    passed = []
    ip_info = {}
    exit_details = {}
    for attempt in range(1, AVAILABILITY_RETRY_MAX + 1):
        print(f"\n[可用性检测] 第 {attempt} 轮检测...")
        passed, ip_info, exit_details = availability_filter_candidates(candidates)
        if passed:
            print(f"✅ 可用性检测通过 {len(passed)} 个节点")
            return passed, ip_info, exit_details
        if attempt < AVAILABILITY_RETRY_MAX:
            print(f"⚠️ 本轮可用性检测通过率为 0%，等待 {AVAILABILITY_RETRY_DELAY} 秒后重试...")
            time.sleep(AVAILABILITY_RETRY_DELAY)

    print(f"❌ 可用性检测经 {AVAILABILITY_RETRY_MAX} 轮重试后仍无节点通过。")
    send_wxpusher_notification(
        content=f"IP 可用性检测经 {AVAILABILITY_RETRY_MAX} 轮重试后仍无节点通过，已跳过过滤，使用原候选列表继续。",
        summary="可用性检测全部失败"
    )
    return candidates, {}, {}

def measure_bandwidth_curl(node_str):
    m = IP_PORT_PATTERN.match(node_str)
    if not m:
        return (node_str, 0)
    ip, port = m.group(1), m.group(2)

    null_device = "NUL" if sys.platform == "win32" else "/dev/null"
    curl_cmd = [
        "curl", "-s", "-o", null_device,
        "-w", "%{size_download} %{time_total}",
        "--resolve", f"speed.cloudflare.com:{port}:{ip}",
        "--connect-timeout", str(BANDWIDTH_CONNECT_TIMEOUT),
        "--max-time", str(BANDWIDTH_TIMEOUT),
        "--insecure",
        BANDWIDTH_URL
    ]

    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=BANDWIDTH_TIMEOUT + BANDWIDTH_PROCESS_BUFFER)
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split()
            if len(parts) >= 2:
                size_bytes = float(parts[0])
                time_total = float(parts[1])
                if time_total > 0 and size_bytes > 0:
                    speed_mbps = (size_bytes * 8) / (time_total * 1000 * 1000)
                    return (node_str, speed_mbps)
    except Exception:
        pass
    return (node_str, 0)

def bandwidth_filter(candidates):
    if not candidates:
        return []

    if not shutil.which("curl"):
        print("⚠️ 未检测到 curl 命令，带宽测速将跳过。")
        return []

    print(f"\n开始带宽测速（对前 {len(candidates)} 个节点，并发 {BANDWIDTH_WORKERS}，超时 {BANDWIDTH_TIMEOUT}s）...")
    results = []
    completed = 0
    total = len(candidates)
    last_print = time.time()

    with ThreadPoolExecutor(max_workers=BANDWIDTH_WORKERS) as executor:
        futures = {executor.submit(measure_bandwidth_curl, node): node for node in candidates}
        for future in as_completed(futures):
            completed += 1
            node, speed = future.result()
            if speed > 0:
                results.append((node, speed))
            now = time.time()
            if now - last_print >= PROGRESS_PRINT_INTERVAL or completed == total:
                print(f"\r[带宽测速] 进度：{completed}/{total} ({(completed/total)*100:.1f}%)", end="", flush=True)
                last_print = now

    print()
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def batch_update_cloudflare_dns(ip_list, ip_info=None, full_bw_results=None, target_count=None, latency_map=None):
    if not cfg.get("CF_ENABLED", False):
        print("Cloudflare DNS 批量更新未启用。")
        return

    if target_count is None:
        target_count = cfg.get("DNS_UPDATE_TARGET_COUNT", 15)

    dns_ip_list = []
    dns_node_list = []
    filtered_by_port = 0
    filtered_by_ipv6 = 0
    filtered_by_country = 0

    if full_bw_results and ip_info:
        blocked_set = set()
        if cfg.get("FILTER_BLOCKED_COUNTRIES_ENABLED", False):
            blocked_set = {c.upper() for c in cfg.get("BLOCKED_COUNTRIES", [])}

        for node_str, speed in full_bw_results:
            if ':' in node_str:
                port = node_str.split(':')[1].split('#')[0]
                if port != '443':
                    filtered_by_port += 1
                    continue

            if cfg.get("FILTER_IPV6_AVAILABILITY", False):
                stack = ip_info.get(node_str, "unknown")
                if stack == "ipv6_only":
                    filtered_by_ipv6 += 1
                    continue

            if blocked_set and '#' in node_str:
                country = node_str.split('#')[-1].upper()
                if country in blocked_set:
                    filtered_by_country += 1
                    continue

            pure_ip = node_str.split(':')[0]
            dns_ip_list.append(pure_ip)
            dns_node_list.append(node_str)

            if len(dns_ip_list) >= target_count:
                break

        filter_parts = []
        if filtered_by_port > 0:
            filter_parts.append(f"非443端口过滤({filtered_by_port}个)")
        if cfg.get("FILTER_IPV6_AVAILABILITY", False):
            filter_parts.append(f"IPv6落地过滤({filtered_by_ipv6}个)")
        if cfg.get("FILTER_BLOCKED_COUNTRIES_ENABLED", False):
            filter_parts.append(f"屏蔽国家过滤({filtered_by_country}个)")
        filter_str = " + ".join(filter_parts) if filter_parts else "无过滤"
        print(f"从 {len(full_bw_results)} 个测速节点中筛选出 {len(dns_ip_list)} 个节点用于 DNS 更新（{filter_str}）。")

    if not dns_ip_list:
        if ip_list:
            print("⚠️ 未能从完整测速结果构建 DNS 列表，降级使用 ip.txt 中的 IP。")
            dns_ip_list = ip_list
            dns_node_list = ip_list
        else:
            msg = "没有可用的 IP 用于 DNS 更新，跳过。"
            print(msg)
            send_wxpusher_notification(content=msg, summary="DNS 更新跳过")
            return

    seen = set()
    unique_ips = []
    unique_nodes = []
    for ip, node in zip(dns_ip_list, dns_node_list):
        if ip not in seen:
            seen.add(ip)
            unique_ips.append(ip)
            unique_nodes.append(node)
    dns_ip_list = unique_ips
    dns_node_list = unique_nodes

    print(f"\n准备将以下 {len(dns_ip_list)} 个 IP 批量更新到 Cloudflare DNS:")
    speed_map = {}
    if full_bw_results:
        speed_map = {node: speed for node, speed in full_bw_results}
    for i, (ip, node) in enumerate(zip(dns_ip_list, dns_node_list), 1):
        speed = speed_map.get(node, 0)
        lat_ms = float('inf')
        if latency_map and node in latency_map:
            lat_ms = latency_map[node] * 1000
        if lat_ms != float('inf'):
            print(f"{i}. {node} 速度 {speed:.2f} Mbps 延迟 {lat_ms:.2f} ms")
        else:
            print(f"{i}. {ip} 速度 {speed:.2f} Mbps")

    headers = {
        "Authorization": f"Bearer {cfg['CF_API_TOKEN']}",
        "Content-Type": "application/json"
    }
    zone_id = cfg['CF_ZONE_ID']
    record_name = cfg['CF_DNS_RECORD_NAME']
    ttl = cfg.get('CF_TTL', 120)
    proxied = cfg.get('CF_PROXIED', False)

    max_retries = cfg.get('DNS_UPDATE_MAX_RETRIES', 5)
    retry_delay = cfg.get('DNS_UPDATE_RETRY_DELAY', 10)

    for attempt in range(1, max_retries + 1):
        print(f"\n[DNS 更新] 尝试 {attempt}/{max_retries}...")
        try:
            list_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&name={record_name}"
            response = requests.get(list_url, headers=headers, timeout=(CF_DNS_CONNECT_TIMEOUT, CF_DNS_READ_TIMEOUT))
            response.raise_for_status()
            result = response.json()
            if not result.get('success'):
                error_detail = result.get('errors')
                raise Exception(f"查询 DNS 记录失败: {error_detail}")

            existing_records = result.get('result', [])
            deletes = [{"id": rec["id"]} for rec in existing_records]
            posts = [
                {
                    "name": record_name,
                    "type": "A",
                    "content": ip,
                    "ttl": ttl,
                    "proxied": proxied
                }
                for ip in dns_ip_list
            ]

            batch_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/batch"
            payload = {"deletes": deletes, "posts": posts}
            response = requests.post(batch_url, headers=headers, json=payload, timeout=(CF_DNS_CONNECT_TIMEOUT, CF_DNS_READ_TIMEOUT))
            response.raise_for_status()
            result = response.json()
            if not result.get('success'):
                error_detail = result.get('errors')
                raise Exception(f"批量更新失败: {error_detail}")

            success_msg = f"✅ Cloudflare DNS 批量更新成功！已将 {record_name} 指向 {len(dns_ip_list)} 个 IP。"
            print(success_msg)
            print("   注意：DNS 解析将随机返回这些 IP 中的一个，实现负载均衡。")
            return

        except Exception as e:
            error_msg = f"[尝试 {attempt}/{max_retries}] DNS 更新出错: {e}"
            print(error_msg)
            if attempt < max_retries:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                final_error = f"❌ Cloudflare DNS 更新失败，已重试 {max_retries} 次，错误：{e}"
                print(final_error)
                send_wxpusher_notification(content=final_error, summary="DNS 更新失败")

def sync_to_github():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if sys.platform == "win32":
        script_name = "git_sync.ps1"
        interpreter = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File"]
        creationflags = subprocess.CREATE_NO_WINDOW
    else:
        script_name = "git_sync.sh"
        interpreter = ["bash"]
        creationflags = 0

    script_path = os.path.join(script_dir, script_name)
    if not os.path.exists(script_path):
        print(f"⚠️ 未找到 {script_name}，跳过 GitHub 同步。")
        return

    if sys.platform != "win32":
        try:
            os.chmod(script_path, 0o755)
        except Exception:
            pass

    max_retries = cfg.get('GITHUB_SYNC_MAX_RETRIES', 5)
    retry_delay = cfg.get('GITHUB_SYNC_RETRY_DELAY', 10)
    process_timeout = cfg.get('GIT_SYNC_PROCESS_TIMEOUT', 180)

    for attempt in range(1, max_retries + 1):
        print(f"\n正在同步到 GitHub (尝试 {attempt}/{max_retries})...")
        try:
            cmd = interpreter + [script_path]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creationflags
            )

            try:
                stdout, stderr = process.communicate(timeout=process_timeout)
                if process.returncode == 0:
                    print("✅ 已自动推送到 GitHub。")
                    return
                else:
                    print(f"❌ 推送失败 (退出码 {process.returncode})")
                    if stderr:
                        print(f"错误信息: {stderr.strip()}")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"❌ 推送超时（超过 {process_timeout} 秒）")
        except Exception as e:
            print(f"❌ 推送过程异常: {e}")

        if attempt < max_retries:
            print(f"等待 {retry_delay} 秒后重试...")
            time.sleep(retry_delay)

    send_wxpusher_notification(
        content=f"GitHub 推送失败，已重试 {max_retries} 次，请检查网络或仓库状态。",
        summary="GitHub 推送失败"
    )
    print(f"⚠️ 已尝试 {max_retries} 次推送，均失败，请检查网络或 GitHub 仓库状态。")

def main():
    mode_str = f"全局最优{GLOBAL_TOP_N}个" if USE_GLOBAL_MODE else f"每个国家最优{PER_COUNTRY_TOP_N}个"
    print(f"当前模式：{mode_str}，每个节点测试 {TCP_PROBES} 次 TCP 连接")
    print(f"最低成功率要求：{MIN_SUCCESS_RATE*100:.0f}%")
    print(f"IP 可用性二次筛选：{'启用' if TEST_AVAILABILITY else '禁用'}（仅对候选节点）")
    print(f"IPv6 客户端 IP 过滤（仅作用于DNS更新环节）：{'启用' if FILTER_IPV6_AVAILABILITY else '禁用'}")
    print(f"屏蔽国家过滤（仅作用于DNS更新环节）：{'启用' if FILTER_BLOCKED_COUNTRIES_ENABLED else '禁用'}，屏蔽国家：{', '.join(BLOCKED_COUNTRIES)}")
    print(f"带宽测速候选数：{BANDWIDTH_CANDIDATES}，测速文件大小：{BANDWIDTH_SIZE_MB} MB，超时：{BANDWIDTH_TIMEOUT}s")
    if FILTER_COUNTRIES_ENABLED:
        print(f"国家过滤：启用，允许国家：{', '.join(ALLOWED_COUNTRIES)}")

    nodes = fetch_nodes()
    if not nodes:
        print("没有获取到任何有效节点，退出。")
        sys.exit(1)

    if FILTER_COUNTRIES_ENABLED and ALLOWED_COUNTRIES:
        before = len(nodes)
        allowed_set = {c.upper() for c in ALLOWED_COUNTRIES}
        filtered_nodes = []
        for node in nodes:
            parts = node.split('#')
            if len(parts) == 2 and parts[1].upper() in allowed_set:
                filtered_nodes.append(node)
        nodes = filtered_nodes
        after = len(nodes)
        print(f"\n国家过滤（测试前）：{before} -> {after} 个节点（允许国家：{', '.join(allowed_set)}）")
        if not nodes:
            print("⚠️ 过滤后无任何节点，退出程序。")
            sys.exit(0)

    total = len(nodes)
    print(f"开始 TCP 连接测试（超时 {TIMEOUT}s，并发 {MAX_WORKERS}）...")

    results = []
    completed = 0
    last_print = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(test_node, node): node for node in nodes}
        for future in as_completed(futures):
            completed += 1
            res = future.result()
            if res:
                results.append(res)
            now = time.time()
            if now - last_print >= PROGRESS_PRINT_INTERVAL or completed == total:
                print(f"\r进度：{completed}/{total} ({(completed/total)*100:.1f}%)", end="", flush=True)
                last_print = now

    print("\nTCP 测试完成！")
    if not results:
        print("没有通过成功率筛选的节点，请检查网络或降低 MIN_SUCCESS_RATE。")
        sys.exit(0)

    results.sort(key=lambda x: (-x[3], x[1]))
    latency_map = {node: lat for node, lat, _, _ in results}

    if USE_GLOBAL_MODE:
        candidates = [node for node, _, _, _ in results[:BANDWIDTH_CANDIDATES]]
        print(f"\nTCP 最优前 {len(candidates)} 个节点进入候选池。")
    else:
        country_nodes = defaultdict(list)
        for node_str, lat, country, succ in results:
            country_nodes[country].append((node_str, lat, succ))

        total_countries = len(country_nodes)
        base_limit = max(1, BANDWIDTH_CANDIDATES // total_countries)
        candidates = []
        for country, nodes in country_nodes.items():
            nodes_sorted = sorted(nodes, key=lambda x: (-x[2], x[1]))
            limit = min(len(nodes_sorted), base_limit)
            for node_str, lat, succ in nodes_sorted[:limit]:
                candidates.append(node_str)
        print(f"\n各国家候选池分配：共 {total_countries} 个国家，每国最多 {base_limit} 个候选，总计 {len(candidates)} 个节点进入候选池。")

    if not candidates:
        print("没有候选节点，退出。")
        sys.exit(0)

    candidates_after_availability, avail_ip_info, avail_exit_details = availability_filter_with_retry(candidates)

    bw_results = []
    for attempt in range(1, BANDWIDTH_RETRY_MAX + 1):
        print(f"\n[带宽测速] 第 {attempt} 轮测试...")
        bw_results = bandwidth_filter(candidates_after_availability)
        if bw_results:
            break
        if attempt < BANDWIDTH_RETRY_MAX:
            print(f"⚠️ 本轮测速无有效结果，等待 {BANDWIDTH_RETRY_DELAY} 秒后重试...")
            time.sleep(BANDWIDTH_RETRY_DELAY)

    if not bw_results:
        print("\n⚠️ 带宽测速多次重试仍无有效结果，将使用 TCP 筛选结果作为最终节点。")
        send_wxpusher_notification(
            content=f"带宽测速经 {BANDWIDTH_RETRY_MAX} 轮尝试后仍无有效结果，已降级使用 TCP 排序节点。",
            summary="带宽测速全部失败"
        )
        if USE_GLOBAL_MODE:
            final_selected = [node for node, _, _, _ in results[:GLOBAL_TOP_N]]
        else:
            final_selected = []
            for country, nodes in country_nodes.items():
                nodes_sorted = sorted(nodes, key=lambda x: (-x[2], x[1]))
                for node_str, _, _ in nodes_sorted[:PER_COUNTRY_TOP_N]:
                    final_selected.append(node_str)
    else:
        if USE_GLOBAL_MODE:
            final_selected = [node for node, _ in bw_results[:GLOBAL_TOP_N]]
        else:
            country_speed_nodes = defaultdict(list)
            for node, speed in bw_results:
                country = node.split('#')[-1] if '#' in node else ''
                if country:
                    country_speed_nodes[country].append((node, speed))
            final_selected = []
            for country, nodes in country_speed_nodes.items():
                for node, speed in nodes[:PER_COUNTRY_TOP_N]:
                    final_selected.append(node)
            speed_map = {node: speed for node, speed in bw_results}
            final_selected.sort(key=lambda x: speed_map.get(x, 0), reverse=True)

        print("\n================ 最终优选节点 ================")
        speed_map = {node: speed for node, speed in bw_results}
        for i, node in enumerate(final_selected, 1):
            speed = speed_map.get(node, 0)
            lat_sec = latency_map.get(node, float('inf'))
            if lat_sec != float('inf'):
                print(f"{i}. {node} 速度 {speed:.2f} Mbps 延迟 {lat_sec*1000:.2f} ms")
            else:
                print(f"{i}. {node} 速度 {speed:.2f} Mbps")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for node_str in final_selected:
            f.write(node_str + "\n")
    print(f"\n结果已保存到 {OUTPUT_FILE}（共 {len(final_selected)} 个节点）")

    ip_list = []
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            ip_list = [line.split(':')[0].strip() for line in f if line.strip()]
    except Exception as e:
        print(f"读取 {OUTPUT_FILE} 时发生错误: {e}")

    target_dns_count = GLOBAL_TOP_N if USE_GLOBAL_MODE else PER_COUNTRY_TOP_N
    batch_update_cloudflare_dns(
        ip_list,
        ip_info=avail_ip_info,
        full_bw_results=bw_results,
        target_count=target_dns_count,
        latency_map=latency_map
    )

    sync_to_github()

if __name__ == "__main__":
    main()
