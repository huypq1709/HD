# File: frontend/Dockerfile
# Giai đoạn 1: Build
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Giai đoạn 2: Production
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html