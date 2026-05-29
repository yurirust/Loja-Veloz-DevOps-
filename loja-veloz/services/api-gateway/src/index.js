const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const client = require('prom-client');

const app = express();
const PORT = process.env.PORT || 3000;

// ── Observabilidade: Prometheus ──────────────────────────────────────────────
const register = new client.Registry();
client.collectDefaultMetrics({ register });

const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duração das requisições HTTP em segundos',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.05, 0.1, 0.3, 0.5, 1, 2, 5],
  registers: [register],
});

// Middleware de métricas
app.use((req, res, next) => {
  const end = httpRequestDuration.startTimer();
  res.on('finish', () => {
    end({ method: req.method, route: req.path, status_code: res.statusCode });
  });
  next();
});

// ── Health Check ─────────────────────────────────────────────────────────────
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'api-gateway', timestamp: new Date().toISOString() });
});

// ── Métricas Prometheus ───────────────────────────────────────────────────────
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

// ── Proxy Routes ──────────────────────────────────────────────────────────────
const PEDIDOS_URL    = process.env.PEDIDOS_SERVICE_URL    || 'http://pedidos:8080';
const PAGAMENTOS_URL = process.env.PAGAMENTOS_SERVICE_URL || 'http://pagamentos:8081';
const ESTOQUE_URL    = process.env.ESTOQUE_SERVICE_URL    || 'http://estoque:8082';

app.use('/api/pedidos', createProxyMiddleware({
  target: PEDIDOS_URL,
  changeOrigin: true,
  pathRewrite: { '^/api/pedidos': '' },
  on: { error: (err, req, res) => res.status(502).json({ error: 'Serviço de pedidos indisponível' }) },
}));

app.use('/api/pagamentos', createProxyMiddleware({
  target: PAGAMENTOS_URL,
  changeOrigin: true,
  pathRewrite: { '^/api/pagamentos': '' },
  on: { error: (err, req, res) => res.status(502).json({ error: 'Serviço de pagamentos indisponível' }) },
}));

app.use('/api/estoque', createProxyMiddleware({
  target: ESTOQUE_URL,
  changeOrigin: true,
  pathRewrite: { '^/api/estoque': '' },
  on: { error: (err, req, res) => res.status(502).json({ error: 'Serviço de estoque indisponível' }) },
}));

app.listen(PORT, () => console.log(`API Gateway rodando na porta ${PORT}`));
module.exports = app;
