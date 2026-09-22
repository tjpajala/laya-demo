# syntax=docker/dockerfile:1.7
FROM node:20-slim AS build
WORKDIR /app
COPY package.json ./
RUN --mount=type=cache,target=/root/.npm,id=npm-cache \
    npm install
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
