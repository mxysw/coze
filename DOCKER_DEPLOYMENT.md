# Docker 部署指南

## 快速开始

### 1. 准备 `.env` 配置文件

复制示例配置：
```bash
cp env.example .env
```

编辑 `.env` 填入真实配置：
```env
COZE_JWT_OAUTH_CLIENT_ID=1111625002608
COZE_JWT_OAUTH_PUBLIC_KEY_ID=mLDp5ya0mdLGEcE5V6TFks1XcDYNytytGO4HflChP5o
COZE_JWT_OAUTH_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQD...
-----END PRIVATE KEY-----"
COZE_API_BASE=https://api.coze.cn
COZE_BOT_ID=7574314241218904100
```

### 2. 使用 Docker Compose 部署（推荐）

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务（配置更新后）
docker-compose restart
```

访问：`http://localhost:5000`

### 3. 使用 Docker 命令部署

```bash
# 构建镜像
docker build -t coze-oauth-app .

# 运行容器（从外部 .env 读取配置）
docker run -d \
  --name coze-app \
  -p 5000:5000 \
  --env-file .env \
  coze-oauth-app

# 查看日志
docker logs -f coze-app

# 停止容器
docker stop coze-app

# 删除容器
docker rm coze-app
```

---

## 配置更新

### 更新 Bot ID 或 OAuth 配置

1. 修改 `.env` 文件
2. 重启容器：
   ```bash
   docker-compose restart
   ```

### 使用私钥文件

如果私钥存放在文件里：

1. `.env` 配置：
   ```env
   COZE_JWT_OAUTH_PRIVATE_KEY_FILE_PATH=/app/secrets/coze_private.pem
   ```

2. 挂载私钥文件（修改 `docker-compose.yml`）：
   ```yaml
   services:
     coze-app:
       # ...
       volumes:
         - ./coze_private.pem:/app/secrets/coze_private.pem:ro
   ```

3. 重启：
   ```bash
   docker-compose up -d
   ```

---

## 生产部署配置

### 1. 修改端口映射

编辑 `docker-compose.yml`：
```yaml
ports:
  - "8080:5000"  # 改成你需要的端口
```

### 2. 配置 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. 启用 HTTPS（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 健康检查

容器内置健康检查接口：

```bash
# 手动检查
curl http://localhost:5000/healthz

# 查看容器健康状态
docker ps
# 或
docker-compose ps
```

---

## 多容器部署（负载均衡）

如果需要横向扩展：

```yaml
version: '3.8'

services:
  coze-app:
    build: .
    env_file:
      - .env
    deploy:
      replicas: 3  # 运行 3 个实例

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - coze-app
```

---

## 日志管理

### 查看实时日志
```bash
docker-compose logs -f coze-app
```

### 限制日志大小
编辑 `docker-compose.yml`：
```yaml
services:
  coze-app:
    # ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 备份与恢复

### 备份配置
```bash
# 备份 .env
cp .env .env.backup

# 导出容器配置
docker inspect coze-app > container-config.json
```

### 迁移到新服务器
```bash
# 1. 打包镜像
docker save coze-oauth-app:latest | gzip > coze-app.tar.gz

# 2. 传输到新服务器
scp coze-app.tar.gz user@new-server:/path/

# 3. 在新服务器加载
docker load < coze-app.tar.gz

# 4. 复制 .env 并启动
docker-compose up -d
```

---

## 常见问题

### 1. 容器启动失败

检查日志：
```bash
docker-compose logs coze-app
```

常见原因：
- `.env` 配置错误或缺失
- 端口被占用（改 `docker-compose.yml` 端口映射）

### 2. 无法访问服务

```bash
# 检查容器状态
docker-compose ps

# 检查端口监听
netstat -tlnp | grep 5000

# 检查防火墙
sudo ufw status
```

### 3. 配置更新不生效

```bash
# 完全重建容器
docker-compose down
docker-compose up -d --build
```

---

## 性能优化

### 1. 调整 Worker 数量

编辑 `Dockerfile`，修改 Gunicorn 配置：
```dockerfile
CMD ["gunicorn", "-w", "8", "-b", "0.0.0.0:5000", "--timeout", "120", "server:app"]
# -w 8 表示 8 个 worker 进程
```

### 2. 资源限制

编辑 `docker-compose.yml`：
```yaml
services:
  coze-app:
    # ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## 监控

### 使用 Docker Stats

```bash
docker stats coze-app
```

### Prometheus + Grafana（可选）

在 `docker-compose.yml` 添加监控服务：
```yaml
services:
  # ... 现有服务

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

---

## 清理

```bash
# 停止并删除容器
docker-compose down

# 删除镜像
docker rmi coze-oauth-app

# 清理未使用的镜像和缓存
docker system prune -a
```

---

## 自动部署（CI/CD）

### GitHub Actions 示例

创建 `.github/workflows/deploy.yml`：
```yaml
name: Deploy to Docker

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push
        run: |
          docker build -t coze-oauth-app .
          docker save coze-oauth-app | gzip > app.tar.gz
      
      - name: Deploy to server
        uses: appleboy/scp-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          source: "app.tar.gz,docker-compose.yml"
          target: "/opt/coze-app"
```

---

需要帮助？查看主 `README.md` 或提交 Issue。

