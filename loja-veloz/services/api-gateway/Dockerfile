# ─── Stage 1: Build ───────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar apenas manifests de dependências primeiro (cache de camadas)
COPY package*.json ./
RUN npm ci --only=production

# ─── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM node:20-alpine AS runtime

# Segurança: usuário não-root
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

# Copiar apenas artefatos necessários do stage anterior
COPY --from=builder /app/node_modules ./node_modules
COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

CMD ["node", "src/index.js"]
