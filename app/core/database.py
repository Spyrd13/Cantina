import os
import logging
from pathlib import Path

# dotenv is optional at runtime; handle missing package gracefully
try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - runtime fallback
    load_dotenv = lambda *args, **kwargs: None
    logging.getLogger(__name__).warning(
        "python-dotenv not installed; .env files will not be loaded. Install with 'pip install python-dotenv'."
    )

from sqlmodel import SQLModel, create_engine

# Carregar variáveis de ambiente
env_file = Path(__file__).parent.parent.parent / ".env.local"
if not env_file.exists():
    env_file = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_file)

# Configurações
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/cantina.db")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ENV = os.getenv("ENV", "development")

# Configurar logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Engine sem echo em produção
engine = create_engine(
    DATABASE_URL,
    echo=DEBUG,  # Apenas em desenvolvimento
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Criar tabelas se não existirem
def init_db():
    """Inicializa o banco de dados com as tabelas necessárias."""
    try:
        SQLModel.metadata.create_all(engine)
        logging.info(f"Banco de dados inicializado: {DATABASE_URL}")
    except Exception as e:
        logging.error(f"Erro ao inicializar banco de dados: {e}")
        raise
