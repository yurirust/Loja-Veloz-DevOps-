from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
import uuid, logging, httpx, os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    pagamento_gateway_url: str = "https://sandbox.gateway-externo.com"
    pagamento_gateway_token: str = "token-sandbox"
    app_version: str = "1.0.0"

settings = Settings()

app = FastAPI(title="Serviço de Pagamentos", version=settings.app_version)
Instrumentator().instrument(app).expose(app)
FastAPIInstrumentor.instrument_app(app)

# Simulação de estado em memória (em prod: usar banco)
pagamentos_db: dict = {}

class ProcessarPagamentoRequest(BaseModel):
    pedido_id: str  = Field(..., description="ID do pedido")
    valor:     float = Field(..., gt=0)
    metodo:    str  = Field(..., description="cartao_credito | pix | boleto")

class PagamentoResponse(BaseModel):
    id:        str
    pedido_id: str
    valor:     float
    metodo:    str
    status:    str

@app.get("/health")
def health():
    return {"status": "ok", "service": "pagamentos", "version": settings.app_version}

@app.post("/pagamentos", response_model=PagamentoResponse, status_code=201)
async def processar_pagamento(req: ProcessarPagamentoRequest):
    """
    Integra com gateway externo de pagamento.
    Em sandbox, simula aprovação para facilitar testes.
    """
    pagamento_id = str(uuid.uuid4())
    logger.info(f"Processando pagamento: pedido={req.pedido_id} valor={req.valor} metodo={req.metodo}")

    # Simulação de chamada ao gateway externo
    # Em produção: chamar settings.pagamento_gateway_url com Bearer settings.pagamento_gateway_token
    status = "APROVADO"  # Sandbox sempre aprova

    pagamento = {
        "id": pagamento_id,
        "pedido_id": req.pedido_id,
        "valor": req.valor,
        "metodo": req.metodo,
        "status": status,
    }
    pagamentos_db[pagamento_id] = pagamento
    logger.info(f"Pagamento {pagamento_id} -> {status}")
    return pagamento

@app.get("/pagamentos/{pagamento_id}", response_model=PagamentoResponse)
def buscar_pagamento(pagamento_id: str):
    p = pagamentos_db.get(pagamento_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return p
