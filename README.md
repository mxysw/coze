# Coze OAuth JWT 会话隔离方案

基于扣子 OAuth JWT 鉴权实现多用户会话隔离的完整解决方案。每个访客拥有独立的聊天记录和用户变量，互不干扰。

---

## 项目架构

```
E:\coze\
├── server.py              # Flask 后端服务（提供 API + 静态页面）
├── coze_oauth.py          # OAuth JWT 封装（基于 cozepy SDK）
├── index.html             # 前端页面
├── index.js               # 前端逻辑（Chat SDK 集成）
├── main.css               # 样式文件
├── requirements.txt       # Python 依赖
├── .env                   # 配置文件（OAuth 密钥等）
└── README.md              # 本文档
```

---

## 功能特性

✅ **会话隔离**：不同用户的聊天记录、用户变量完全隔离  
✅ **自动刷新**：Token 过期自动续期，用户无感知  
✅ **简单部署**：单个 Flask 服务同时提供前后端  
✅ **官方 SDK**：使用 `cozepy` 官方 SDK，稳定可靠  

---

## 快速开始

### 1. 环境准备

- Python 3.8+
- 扣子账号及 OAuth JWT 应用

### 2. 创建 OAuth 应用

1. 访问 https://www.coze.cn/open/oauth/apps
2. 创建"服务应用（JWT）"类型的 OAuth 应用
3. 生成公私钥对并上传公钥：
   ```bash
   # 生成私钥
   openssl genrsa -out coze_private.pem 2048
   
   # 导出公钥
   openssl rsa -in coze_private.pem -pubout -out coze_public.pem
   ```
4. 记录以下信息：
   - `client_id`（应用 ID）
   - `public_key_id`（上传公钥后生成的 ID）
   - 私钥内容（`coze_private.pem`）

### 3. 配置 `.env`

在项目根目录创建 `.env` 文件（顶格写，不要有行首空格）：

```env
COZE_JWT_OAUTH_CLIENT_ID=你的client_id
COZE_JWT_OAUTH_PUBLIC_KEY_ID=你的public_key_id
COZE_JWT_OAUTH_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQD...
（完整私钥内容，保持 PEM 格式换行）
...
-----END PRIVATE KEY-----"
COZE_API_BASE=https://api.coze.cn
```

**或使用私钥文件**：

```env
COZE_JWT_OAUTH_CLIENT_ID=你的client_id
COZE_JWT_OAUTH_PUBLIC_KEY_ID=你的public_key_id
COZE_JWT_OAUTH_PRIVATE_KEY_FILE_PATH=./coze_private.pem
COZE_API_BASE=https://api.coze.cn
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置 Bot ID

编辑 `index.js`，修改第 1 行：

```javascript
const BOT_ID = '你的Bot ID';  // 在扣子控制台的 Bot 页面获取
```

### 6. 启动服务

```bash
flask --app server run
```

或指定端口：

```bash
flask --app server run --port 8080
```

### 7. 访问测试

浏览器打开 `http://127.0.0.1:5000/`，聊天窗口应正常加载。

---

## 验证会话隔离

1. **正常浏览器**访问 `http://127.0.0.1:5000/`，发送消息 A
2. **隐私/无痕模式**访问同一地址，发送消息 B
3. 两个窗口的聊天记录完全独立，互不可见 ✅

---

## 核心原理

### 会话隔离机制

```
用户访问 → 前端生成唯一 UID（localStorage）
         ↓
    POST /api/chat-token {userId: "user_xxx"}
         ↓
    后端签发 JWT（payload 含 session_name=user_xxx）
         ↓
    调用 Coze OAuth API 换取 access_token
         ↓
    前端用 token 初始化 Chat SDK
         ↓
    Coze 按 session_name 隔离会话
```

### 关键参数

- **`session_name`**：JWT payload 里的字段，Coze 用它区分不同子会话
- **`aud`**：必须是 `api.coze.cn`（域名，不带 `https://`）
- **`token_type`**：前端 auth 配置必须用 `'token'`，不是 `'jwt'`

---

## API 接口

### `POST /api/chat-token`

为指定用户签发 OAuth access token。

**请求：**

```json
{
  "userId": "user_d36f2e58-610b-4d80-93c4-3c33a87b2855"
}
```

**响应：**

```json
{
  "token": "czs_xxx...",
  "token_type": "Bearer",
  "expires_in": 1763662021,
  "expires_at": 3527320440
}
```

### `GET /healthz`

健康检查接口。

**响应：**

```json
{
  "status": "ok"
}
```

---

## 部署多个 Bot

### 方案 A：同一页面切换 Bot

修改 `index.js` 的 `BOT_ID` 即可。

### 方案 B：多个独立页面

1. 复制 `index.html` → `bot2.html`
2. 复制 `index.js` → `bot2.js`
3. 修改 `bot2.html` 引用 `bot2.js`：
   ```html
   <script src="./bot2.js"></script>
   ```
4. 在 `bot2.js` 里改 `BOT_ID`
5. 访问 `http://127.0.0.1:5000/bot2.html`

后端 `/api/chat-token` 无需改动，可复用。

---

## 常见问题

### 1. Token 返回 `null`

**原因**：公私钥不匹配或 OAuth 应用配置错误。

**解决**：
- 确认 `.env` 里的 `public_key_id` 和扣子控制台一致
- 验证私钥对应的公钥是否已正确上传
- 查看 Flask 日志里的 `[DEBUG]` 信息

### 2. 前端报错 `The auth type (unauth) is unsupported`

**原因**：`auth.type` 配置错误或 token 获取失败。

**解决**：
- 确认 `index.js` 里 `auth.type` 是 `'token'`
- 打开浏览器 F12 → Network，检查 `/api/chat-token` 是否返回 200
- 查看 Console 是否有 `[DEBUG] Got token` 日志

### 3. 会话未隔离（不同用户看到相同聊天记录）

**原因**：未正确传递 `session_name` 或使用了旧的 Access Token 鉴权。

**解决**：
- 确认 `coze_oauth.py` 调用了 `jwt_app.get_access_token(session_name=...)`
- 清除浏览器 localStorage，重新生成 UID

### 4. Token 过期后无法续期

**原因**：`onRefreshToken` 未配置或实现错误。

**解决**：
- 确认 `index.js` 里 `auth.onRefreshToken` 存在且正确调用 `fetchChatToken`

---

## 安全注意事项

1. **私钥保护**：`.env` 和 `.pem` 文件只放服务端，添加到 `.gitignore`
2. **HTTPS 部署**：生产环境必须使用 HTTPS
3. **CORS 配置**：如前后端分离部署，正确配置 CORS 白名单
4. **Token 有效期**：可通过 `COZE_ACCESS_TOKEN_TTL` 环境变量调整（默认 3600 秒）

---

## 生产部署建议

### 使用 Gunicorn（推荐）

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 server:app
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker 部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "server:app"]
```

构建运行：

```bash
docker build -t coze-oauth-app .
docker run -p 8080:8080 --env-file .env coze-oauth-app
```

---

## 技术栈

- **后端**：Flask + cozepy SDK
- **前端**：Coze Chat SDK (WebChatClient)
- **鉴权**：OAuth 2.0 JWT Bearer Token
- **会话隔离**：`session_name` 参数

---

## 参考文档

- [扣子 OAuth JWT 文档](https://www.coze.cn/docs/developer_guides/oauth_jwt)
- [扣子 Chat SDK 文档](https://www.coze.cn/docs/developer_guides/install_web_sdk)
- [会话隔离方案](https://www.coze.cn/docs/developer_guides/session_isolation)
- [cozepy SDK](https://github.com/coze-dev/coze-py)

---

## 项目维护

如需更新：

1. **更换 Bot**：修改 `index.js` 的 `BOT_ID`
2. **更换 OAuth 应用**：更新 `.env` 配置并重启服务
3. **升级依赖**：`pip install --upgrade cozepy`

---

## 许可

MIT License

---

## 联系方式

如有问题，请参考扣子官方文档或提交 Issue。

