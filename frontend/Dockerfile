# 前端构建 + nginx 运行镜像(多阶段)
# 构建上下文为 frontend/ 目录,由仓库根 docker-compose.yml 引用
FROM node:20-alpine AS build
WORKDIR /app

# npm ci 严格按 package-lock.json 安装,保证可复现构建
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

FROM nginx:stable-alpine AS runtime

# 统一 nginx 配置:SPA fallback + /api 反代到 compose 内 backend 服务
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# 无需 curl/wget 依赖的健检由 busybox wget 提供(alpine 自带)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q --spider http://localhost/index.html || exit 1

CMD ["nginx", "-g", "daemon off;"]
