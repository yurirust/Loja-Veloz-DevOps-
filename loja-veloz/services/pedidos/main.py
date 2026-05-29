from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, Column, String, Float, DateTime, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import uuid, enum, datetime, os, logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

# ── Configuração via variáveis de ambiente (12-Factor) ────────────────────────
class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@postgres:5432/loja_veloz"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    otel_exporter_otlp_endpoint: str = "http://jaeger:4317"
    app_version: str = "1.0.0"

settings = Settings()

# ── OpenTelemetry ─────────────────────────────────────────────────────────────
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# ── Banco de dados ────────────────────────────────────────────────────────────
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase): pass

class StatusPedido(str, enum.Enum):
    CRIADO = "CRIADO"
    PAGO = "PAGO"
    CANCELADO = "CANCELADO"

class PedidoDB(Base):
    __tablename__ = "pedidos"
    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cliente_id    = Column(String, nullable=False)
    produto_id    = Column(String, nullable=False)
    quantidade    = Column(Float, nullable=False)
    valor_total   = Column(Float, nullable=False)
    status        = Column(SAEnum(StatusPedido), default=StatusPedido.CRIADO)
    criado_em     = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ── Schemas Pydantic ──────────────────────────────────────────────────────────
class CriarPedidoRequest(BaseModel):
    cliente_id:  str   = Field(..., description="ID do cliente")
    produto_id:  str   = Field(..., description="ID do produto")
    quantidade:  float = Field(..., gt=0, description="Quantidade solicitada")
    valor_total: float = Field(..., gt=0, description="Valor total do pedido")

class PedidoResponse(BaseModel):
    id:          str
    cliente_id:  str
    produto_id:  str
    quantidade:  float
    valor_total: float
    status:      StatusPedido
    criado_em:   datetime.datetime

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Serviço de Pedidos", version=settings.app_version)
Instrumentator().instrument(app).expose(app)
FastAPIInstrumentor.instrument_app(app)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok", "service": "pedidos", "version": settings.app_version}

@app.post("/pedidos", response_model=PedidoResponse, status_code=201)
def criar_pedido(req: CriarPedidoRequest, db: Session = Depends(get_db)):
    with tracer.start_as_current_span("criar_pedido") as span:
        span.set_attribute("cliente.id", req.cliente_id)
        span.set_attribute("produto.id", req.produto_id)

        pedido = PedidoDB(**req.model_dump())
        db.add(pedido)
        db.commit()
        db.refresh(pedido)

        logger.info(f"Pedido criado: id={pedido.id} cliente={req.cliente_id}")
        # TODO: publicar evento "PedidoCriado" no RabbitMQ/Kafka
        return pedido

@app.get("/pedidos/{pedido_id}", response_model=PedidoResponse)
def buscar_pedido(pedido_id: str, db: Session = Depends(get_db)):
    pedido = db.query(PedidoDB).filter(PedidoDB.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido

@app.get("/pedidos", response_model=list[PedidoResponse])
def listar_pedidos(db: Session = Depends(get_db)):
    return db.query(PedidoDB).all()
