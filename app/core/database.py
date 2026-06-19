import os
import sys
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


# ------------------------------------------------------------------ #
#  Caminho do banco de dados                                          #
# ------------------------------------------------------------------ #

if getattr(sys, 'frozen', False):
    # Rodando empacotado (flet build)
    # Salva em AppData/Roaming/CantinaTUFI para não precisar de admin
    BASE_DIR = Path(os.environ.get("APPDATA", Path.home())) / "CantinaTUFI"
else:
    # Rodando em desenvolvimento — usa a pasta do projeto
    BASE_DIR = Path(__file__).parent.parent.parent

DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)

# Carregar variáveis de ambiente (só em desenvolvimento)
if not getattr(sys, 'frozen', False):
    env_file = BASE_DIR / ".env.local"
    if not env_file.exists():
        env_file = BASE_DIR / ".env"
    load_dotenv(env_file)

# Configurações
_default_db = f"sqlite:///{DB_DIR}/cantina.db"
DATABASE_URL = os.getenv("DATABASE_URL", _default_db)
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ENV = os.getenv("ENV", "development")

# Configurar logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Engine
engine = create_engine(
    DATABASE_URL,
    echo=DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)


# ------------------------------------------------------------------ #
#  Inicialização                                                      #
# ------------------------------------------------------------------ #

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias."""
    try:
        SQLModel.metadata.create_all(engine)
        logging.info(f"Banco de dados inicializado: {DATABASE_URL}")
    except Exception as e:
        logging.error(f"Erro ao inicializar banco de dados: {e}")
        raise