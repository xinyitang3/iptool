# Cloudflare Workers - IP 优选列表订阅服务

这是一个用于提供 Cloudflare IP 优选列表订阅的服务，读取自 GitHub 仓库中的 ip.txt 文件。

## 功能特性

- 自动获取 GitHub 仓库中的 ip.txt 文件
- 支持缓存，加速访问
- 支持 CORS，可直接用于订阅
- 返回纯文本格式，每行一个 IP

## 部署方法

### 方法一：手动部署

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 进入 **Workers & Pages** → **Create Application** → **Create Worker**
3. 将 `worker.js` 中的全部代码复制粘贴到 Worker 编辑器中
4. 点击 **Save and Deploy**
5. （可选）绑定自定义域名

### 方法二：使用 Wrangler CLI 部署

```bash
# 安装 Wrangler
npm install -g wrangler

# 登录 Cloudflare
wrangler login

# 部署
wrangler deploy
```

## 订阅地址

部署成功后，访问地址为：

- Workers 默认域名：`https://your-worker.your-subdomain.workers.dev/ip`
- 自定义域名：`https://your-domain.com/ip`

## 配置说明

在 `worker.js` 中可以修改以下配置：

```javascript
const CONFIG = {
  // GitHub raw 文件地址（修改为你自己的仓库）
  githubRawUrl: 'https://raw.githubusercontent.com/qq547475331/cfnb/main/ip.txt',

  // 缓存时间（秒）
  cacheMaxAge: 60 * 5,  // 5 分钟

  // 是否启用调试日志
  debug: false
};
```

## GitHub 订阅格式（适用于各种客户端）

很多订阅管理工具支持直接使用 GitHub Raw URL 作为订阅源：

```
https://raw.githubusercontent.com/qq547475331/cfnb/main/ip.txt
```

但如果你需要通过 Workers 中转（解决直连访问 GitHub 速度慢的问题），可以使用：

```
https://your-worker.workers.dev/ip
```

## API 响应

### GET /ip

返回 ip.txt 中的所有 IP 地址，每行一个。

**响应示例**：

```
43.200.87.5
154.219.103.79
54.64.65.213
45.131.179.92
```

**响应头**：

```
Content-Type: text/plain; charset=utf-8
Cache-Control: public, max-age=300
Access-Control-Allow-Origin: *
```

### GET /

返回使用说明页面。

## License

MIT