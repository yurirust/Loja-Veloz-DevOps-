# 🛒 Loja Veloz — Plataforma de Pedidos em Microsserviços

> Projeto acadêmico — Cloud DevOps | UniFECAF  
> Entrega contínua de uma plataforma de pedidos em microsserviços: do Docker Compose ao Kubernetes com observabilidade e CI/CD

---

## Vídeo Pitch
 https://youtu.be/D7rQv9ImzJE

---

## Arquitetura

```
Cliente HTTP
     │
     ▼
┌──────────────┐
│  API Gateway │  :3000  (Node.js / Express)
└──────┬───────┘
       │ proxy
  ┌────┼────┐
  │    │    │
  ▼    ▼    ▼
┌──────┐ ┌──────────┐ ┌─────────┐
│Pedidos│ │Pagamentos│ │ Estoque │
│ :8080 │ │  :8081   │ │  :8082  │
└──┬───┘ └──────────┘ └─────────┘
   │
   ▼
┌──────────┐   ┌───────────┐
│PostgreSQL│   │ RabbitMQ  │
│  :5432   │   │  :5672    │
└──────────┘   └───────────┘

Observabilidade:
  Prometheus :9090 → Grafana :3001
  Jaeger     :16686 (tracing distribuído)
```

---

## 📁 Estrutura do Repositório

```
loja-veloz/
├── services/
│   ├── api-gateway/          # Node.js — proxy e roteamento
│   ├── pedidos/              # Python/FastAPI — CRUD de pedidos
│   ├── pagamentos/           # Python/FastAPI — integração gateway externo
│   └── estoque/              # Python/FastAPI — reserva e baixa de estoque
├── k8s/
│   └── base/                 # Manifests Kubernetes (Deployments, Services, HPA)
│       ├── namespace.yaml
│       ├── configmap.yaml
│       ├── secret.yaml
│       ├── api-gateway.yaml
│       ├── pedidos.yaml
│       ├── pagamentos-estoque.yaml
│       └── hpa.yaml
├── terraform/                # IaC — provisionamento do cluster GKE
├── monitoring/               # Configurações Prometheus e Grafana
├── .github/workflows/        # Pipeline CI/CD (GitHub Actions)
├── docker-compose.yml        # Ambiente local completo
└── .env.example              # Variáveis de ambiente de exemplo
```

---

##  Subindo o Ambiente Local

### Pré-requisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado
- [Git](https://git-scm.com/) instalado

### 1. Clone o repositório
```bash
git clone https://github.com/SEU_USUARIO/loja-veloz-devops.git
cd loja-veloz-devops
```

### 2. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o .env se necessário (para dev, os valores padrão funcionam)
```

### 3. Suba todos os serviços com um único comando
```bash
docker compose up --build
```

### 4. Acesse os serviços
| Serviço        | URL                              |
|----------------|----------------------------------|
| API Gateway    | http://localhost:3000            |
| Pedidos (API)  | http://localhost:8080/docs       |
| Pagamentos     | http://localhost:8081/docs       |
| Estoque        | http://localhost:8082/docs       |
| RabbitMQ UI    | http://localhost:15672           |
| Prometheus     | http://localhost:9090            |
| Grafana        | http://localhost:3001            |
| Jaeger UI      | http://localhost:16686           |

### 5. Testando a API
```bash
# Criar um pedido
curl -X POST http://localhost:3000/api/pedidos \
  -H "Content-Type: application/json" \
  -d '{"cliente_id":"cli-001","produto_id":"prod-001","quantidade":2,"valor_total":99.90}'

# Consultar estoque
curl http://localhost:3000/api/estoque/prod-001

# Processar pagamento
curl -X POST http://localhost:3000/api/pagamentos \
  -H "Content-Type: application/json" \
  -d '{"pedido_id":"<ID_RETORNADO>","valor":99.90,"metodo":"pix"}'
```

### 6. Parar o ambiente
```bash
docker compose down          # Para os containers
docker compose down -v       # Para e remove volumes (limpa o banco)
```

---

## Deploy em Kubernetes

### Pré-requisitos
- `kubectl` configurado apontando para seu cluster
- Imagens já publicadas no registry (feito automaticamente pelo CI/CD)

### Aplicar todos os manifests
```bash
# Criar namespace e configurações
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/base/secret.yaml

# Subir os serviços
kubectl apply -f k8s/base/api-gateway.yaml
kubectl apply -f k8s/base/pedidos.yaml
kubectl apply -f k8s/base/pagamentos-estoque.yaml

# Configurar autoscaling
kubectl apply -f k8s/base/hpa.yaml

# Verificar pods
kubectl get pods -n loja-veloz
```

---

##  Pipeline CI/CD

O pipeline no GitHub Actions (`.github/workflows/ci-cd.yml`) executa automaticamente a cada push na branch `main`:

| Etapa            | O que faz                                      |
|------------------|------------------------------------------------|
| **Testes**       | Lint + testes unitários de todos os serviços   |
| **Build & Push** | Constrói imagens Docker e publica no GHCR      |
| **Deploy**       | Atualiza os pods no Kubernetes via `kubectl`   |
| **Rollback**     | Reverte automaticamente em caso de falha       |

### Secrets necessários no GitHub
```
KUBECONFIG_B64  → kubeconfig do cluster em base64
```

---

##  Observabilidade

### Métricas
- Prometheus coleta métricas de todos os serviços via `/metrics`
- Grafana disponível em `http://localhost:3001` (admin/admin)
- Dashboard sugerido: **Kubernetes / Compute Resources / Namespace**

### Tracing Distribuído
- OpenTelemetry instrumentado em todos os serviços Python
- Jaeger UI em `http://localhost:16686`
- Rastreie o caminho completo: Gateway → Pedidos → Estoque → Pagamentos

### Logs
- Todos os serviços emitem logs estruturados (JSON) para stdout
- Em produção: coletar com Fluentd/Promtail → Loki → Grafana

---

## Infraestrutura como Código (Terraform)

```bash
cd terraform

# Inicializar
terraform init

# Ver o plano de execução
terraform plan -var="project_id=SEU_PROJECT_ID"

# Provisionar o cluster
terraform apply -var="project_id=SEU_PROJECT_ID"

# Obter credenciais do cluster
$(terraform output -raw kubectl_config_command)
```

---

## Segurança

- Todos os containers rodam como **usuário não-root**
- Secrets Kubernetes separados do ConfigMap
- `readOnlyRootFilesystem: true` nos pods
- `allowPrivilegeEscalation: false`
- Capabilities Linux removidas (`drop: ["ALL"]`)
- Namespace com **Pod Security Admission** nível `restricted`

---

##  Referências

- [Kubernetes Docs](https://kubernetes.io/docs/)
- [Docker Docs](https://docs.docker.com/)
- [12-Factor App](https://12factor.net/)
- [Terraform Docs](https://developer.hashicorp.com/terraform/docs)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [Google Cloud — Microservices Reference Architecture](https://cloud.google.com/architecture/microservices-architecture-introduction)
