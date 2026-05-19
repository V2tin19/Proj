FROM node:18-slim
WORKDIR /app

# 使用 server/package.json 安装后端依赖（你们已说明无第三方包，可为空）
COPY server/package*.json ./
RUN npm ci --production --no-audit --no-fund || true

# 复制后端代码
COPY server/ ./server
WORKDIR /app/server

ENV PORT=3000
EXPOSE 3000
CMD ["node", "--enable-source-maps", "index.mjs"]