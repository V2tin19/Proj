FROM node:18-slim
WORKDIR /app

# 只复制 server 代码，不安装依赖（后端无第三方包）
COPY server/ ./server
WORKDIR /app/server

ENV PORT=3000
EXPOSE 3000
CMD ["node", "--enable-source-maps", "index.mjs"]