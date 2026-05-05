/**
 * Cloudflare Workers - IP 优选列表订阅服务
 *
 * 功能：从 GitHub 获取 ip.txt 内容并返回纯文本格式
 * 适用场景：通过自定义域名提供 IP 订阅服务
 */

// ==================== 配置区域 ====================

/**
 * 订阅配置 - 修改这里的地址为你自己的 GitHub 仓库地址
 */
const CONFIG = {
  // GitHub raw 文件地址（修改为你自己的仓库地址）
  githubRawUrl: 'https://raw.githubusercontent.com/qq547475331/cfnb/main/ip.txt',

  // 缓存时间（秒），设置为 0 则禁用缓存
  cacheMaxAge: 300,

  // 是否启用调试日志（生产环境建议关闭）
  debug: false,

  // 备用数据源（当 GitHub 不可用时）
  fallbackIps: [
    '54.238.157.207',
    '54.64.65.213',
    '54.64.6.20'
  ]
};

// ==================== 工具函数 ====================

/**
 * 记录调试日志
 */
function log(...args) {
  if (CONFIG.debug) {
    console.log('[IP-Worker DEBUG]', ...args);
  }
}

/**
 * 生成缓存 key
 */
function getCacheKey(request) {
  return request.url;
}

/**
 * 构建响应
 */
function buildResponse(body, options = {}) {
  const headers = new Headers(options.headers || {});

  headers.set('Content-Type', 'text/plain; charset=utf-8');
  headers.set('Access-Control-Allow-Origin', '*');
  headers.set('Access-Control-Allow-Methods', 'GET, OPTIONS');
  headers.set('Access-Control-Allow-Headers', 'Content-Type');

  if (CONFIG.cacheMaxAge > 0) {
    headers.set('Cache-Control', `public, max-age=${CONFIG.cacheMaxAge}`);
  }

  return new Response(body, {
    status: options.status || 200,
    headers
  });
}

/**
 * 构建 HTML 页面
 */
function buildHtmlPage() {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IP 优选列表订阅服务</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
      min-height: 100vh;
      color: #fff;
      padding: 2rem;
    }
    .container {
      max-width: 800px;
      margin: 0 auto;
    }
    h1 {
      font-size: 2rem;
      margin-bottom: 1rem;
      color: #f39c12;
    }
    .card {
      background: rgba(255,255,255,0.1);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1rem;
      backdrop-filter: blur(10px);
    }
    h2 {
      font-size: 1.2rem;
      margin-bottom: 0.8rem;
      color: #3498db;
    }
    code {
      background: rgba(0,0,0,0.3);
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-family: 'Monaco', 'Menlo', monospace;
      font-size: 0.9rem;
      word-break: break-all;
    }
    .url-box {
      background: rgba(0,0,0,0.4);
      padding: 1rem;
      border-radius: 8px;
      margin: 0.5rem 0;
      word-break: break-all;
    }
    .btn {
      display: inline-block;
      background: #3498db;
      color: white;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      text-decoration: none;
      font-size: 0.9rem;
      margin-top: 0.5rem;
    }
    .btn:hover { background: #2980b9; }
    .footer {
      text-align: center;
      margin-top: 2rem;
      color: #888;
      font-size: 0.85rem;
    }
    pre {
      background: rgba(0,0,0,0.3);
      padding: 1rem;
      border-radius: 8px;
      overflow-x: auto;
      font-size: 0.85rem;
      line-height: 1.5;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🌐 IP 优选列表订阅服务</h1>

    <div class="card">
      <h2>📡 订阅地址</h2>
      <div class="url-box">
        <code id="subscribe-url">加载中...</code>
      </div>
      <a href="#" onclick="copyUrl(); return false;" class="btn">📋 复制订阅地址</a>
    </div>

    <div class="card">
      <h2>📝 使用说明</h2>
      <ol style="padding-left: 1.5rem; line-height: 1.8;">
        <li>复制上方订阅地址</li>
        <li>粘贴到你的订阅管理工具中</li>
        <li>享受自动更新的 Cloudflare 优选 IP！</li>
      </ol>
    </div>

    <div class="card">
      <h2>🔧 配置信息</h2>
      <pre>
GitHub 数据源: ${CONFIG.githubRawUrl}
缓存时间: ${CONFIG.cacheMaxAge} 秒
更新状态: 自动同步
      </pre>
    </div>

    <div class="card">
      <h2>📖 直接访问</h2>
      <ul style="padding-left: 1.5rem; line-height: 2;">
        <li><code>/ip</code> - 获取纯 IP 列表（每行一个）</li>
        <li><code>/</code> - 查看本页面</li>
        <li><code>/health</code> - 健康检查</li>
      </ul>
    </div>

    <div class="footer">
      <p>Powered by Cloudflare Workers | 自动同步自 GitHub</p>
      <p>最近更新: ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })} (CST)</p>
    </div>
  </div>

  <script>
    // 自动设置订阅地址
    document.getElementById('subscribe-url').textContent = window.location.origin + '/ip';

    // 复制功能
    function copyUrl() {
      const url = document.getElementById('subscribe-url').textContent;
      navigator.clipboard.writeText(url).then(() => {
        alert('订阅地址已复制到剪贴板！');
      });
    }
  </script>
</body>
</html>`;
}

// ==================== 核心逻辑 ====================

/**
 * 从 GitHub 获取 IP 列表
 */
async function fetchIpList() {
  log('正在从 GitHub 获取 IP 列表...');

  const response = await fetch(CONFIG.githubRawUrl, {
    cf: {
      cacheTtl: CONFIG.cacheMaxAge,
      cacheEverything: true
    }
  });

  if (!response.ok) {
    throw new Error(`GitHub 请求失败: ${response.status} ${response.statusText}`);
  }

  const text = await response.text();

  // 验证返回的内容是否是有效的 IP 列表
  const lines = text.split('\n').filter(line => {
    const ip = line.trim();
    // 简单的 IP 格式验证
    return ip && /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(ip);
  });

  if (lines.length === 0) {
    throw new Error('未找到有效的 IP 地址');
  }

  log(`成功获取 ${lines.length} 个 IP 地址`);
  return lines.join('\n');
}

/**
 * 处理请求
 */
async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;

  log(`收到请求: ${path}`);

  // 路由处理
  switch (path) {
    case '/ip':
    case '/list':
      // 返回纯 IP 列表（/ip 或 /list 都支持）
      return handleIpRequest(request);

    case '/health':
      // 健康检查
      return buildResponse(JSON.stringify({
        status: 'ok',
        timestamp: new Date().toISOString(),
        source: CONFIG.githubRawUrl
      }), {
        headers: {
          'Content-Type': 'application/json'
        }
      });

    default:
      // 其他路径（包括根路径 /）都返回纯 IP 列表
      return handleIpRequest(request);
  }
}

/**
 * 处理 /ip 请求
 */
async function handleIpRequest(request) {
  const cacheKey = getCacheKey(request);

  // 尝试从缓存获取
  const cache = caches.default;
  let response = await cache.match(cacheKey);

  if (response) {
    log('从缓存返回');
    return response;
  }

  try {
    // 从 GitHub 获取
    const ipList = await fetchIpList();

    response = buildResponse(ipList);

    // 写入缓存
    if (CONFIG.cacheMaxAge > 0) {
      await cache.put(cacheKey, response.clone());
      log('已写入缓存');
    }

    return response;

  } catch (error) {
    log('获取失败:', error.message);

    // 如果有缓存，返回缓存（即使过期）
    if (response) {
      log('返回过期缓存');
      return response;
    }

    // 返回备用数据
    if (CONFIG.fallbackIps.length > 0) {
      log('返回备用数据');
      return buildResponse(
        CONFIG.fallbackIps.join('\n'),
        { status: 200 }
      );
    }

    // 返回错误
    return buildResponse(
      `Error: ${error.message}\n\n请稍后重试或检查数据源配置。`,
      { status: 502 }
    );
  }
}

// ==================== 事件处理 ====================

// 处理 CORS 预检请求
async function handleOptions(request) {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}

// 主事件监听器
addEventListener('fetch', event => {
  const request = event.request;

  // 处理 CORS 预检
  if (request.method === 'OPTIONS') {
    event.respondWith(handleOptions(request));
    return;
  }

  // 处理实际请求
  event.respondWith(handleRequest(request));
});