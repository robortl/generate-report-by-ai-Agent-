# 构建阶段
FROM node:16-alpine as build

WORKDIR /app

# 设置环境变量
ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}

# 复制package.json和package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm install --production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物到Nginx服务目录
COPY --from=build /app/build /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 3000

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"] 