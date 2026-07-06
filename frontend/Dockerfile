# ===================================================
# Stage 1 — Build the Vite SPA
# ===================================================
# Build args (pass at build time):
#   VITE_API_BASE_URL=https://api.your-domain.com
# ===================================================
FROM node:24-alpine AS builder

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ===================================================
# Stage 2 — Serve with Nginx (static SPA)
# ===================================================
FROM nginx:alpine

COPY --from=builder /build/dist /usr/share/nginx/html

# SPA fallback: all routes → index.html
RUN echo 'server { \
  listen 80; \
  root /usr/share/nginx/html; \
  index index.html; \
  location / { \
    try_files $uri $uri/ /index.html; \
  } \
  location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ { \
    expires 1y; \
    add_header Cache-Control "public, immutable"; \
  } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
