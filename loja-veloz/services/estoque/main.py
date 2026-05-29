from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    app_version: str = "1.0.0"

settings = Settings()

app = FastAPI(title="Serviço de Estoque", version=settings.app_version)
Instrumentator().instrument(app).expose(app)
FastAPIInstrumentor.instrument_app(app)

# Simulação de estoque em memória (em prod: usar banco)
estoque_db: dict = {
    "prod-001": {"produto_id": "prod-001", "nome": "Camiseta P", "quantidade": 100},
    "prod-002": {"produto_id": "prod-002", "nome": "Calça M",    "quantidade": 50},
    "prod-003": {"produto_id": "prod-003", "nome": "Tênis 42",   "quantidade": 30},
}

class ReservaRequest(BaseModel):
    produto_id: str  = Field(..., description="ID do produto")
    quantidade: float = Field(..., gt=0, description="Quantidade a reservar")

class EstoqueResponse(BaseModel):
    produto_id: str
    nome:       str
    quantidade: float

@app.get("/health")
def health():
    return {"status": "ok", "service": "estoque", "version": settings.app_version}

@app.get("/estoque/{produto_id}", response_model=EstoqueResponse)
def consultar_estoque(produto_id: str):
    item = estoque_db.get(produto_id)
    if not item:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return item

@app.post("/estoque/reservar", status_code=200)
def reservar_estoque(req: ReservaRequest):
    item = estoque_db.get(req.produto_id)
    if not item:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if item["quantidade"] < req.quantidade:
        raise HTTPException(status_code=409, detail="Estoque insuficiente")
    item["quantidade"] -= req.quantidade
    logger.info(f"Reserva: produto={req.produto_id} qtd={req.quantidade} saldo={item['quantidade']}")
    return {"message": "Reserva realizada", "saldo_restante": item["quantidade"]}

@app.post("/estoque/baixa", status_code=200)
def baixar_estoque(req: ReservaRequest):
    """Confirma a baixa definitiva após pagamento aprovado."""
    item = estoque_db.get(req.produto_id)
    if not item:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    logger.info(f"Baixa definitiva: produto={req.produto_id} qtd={req.quantidade}")
    return {"message": "Baixa realizada com sucesso"}

@app.get("/estoque", response_model=list[EstoqueResponse])
def listar_estoque():
    return list(estoque_db.values())
