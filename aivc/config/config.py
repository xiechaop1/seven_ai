import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets
from typing import Literal
from typing import Dict
import asyncio

CANCELLATION_EVENTS: Dict[str, asyncio.Event] = {}

L = logging.getLogger(__name__)
L.setLevel(logging.DEBUG)
L.propagate = False  # 确保日志不会向上传递

log_file = os.getenv('LOG_FILE', 'api.log')
handler = logging.FileHandler(log_file, encoding='utf-8')
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s')
handler.setFormatter(formatter)

L.addHandler(handler)

logger = logging.getLogger('openai')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# SentenceTransformer 日志
st_logger = logging.getLogger('sentence_transformers')
st_logger.addHandler(handler)

# fastapi日志
class IgnoreHealthCheckFilter(logging.Filter):
    def __init__(self, paths=None):
        super().__init__()
        # 如果没有提供paths，使用默认列表
        self.ignore_paths = paths if paths is not None else [
            'GET /metrics',
            'GET / ',
            'HEAD /check ',
        ]

    def filter(self, record):
        # 检查日志消息是否包含任何忽略路径
        message = record.getMessage()
        return not any(path in message for path in self.ignore_paths)


fastapi_logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s',
        },
    },
    'filters': {
        'endpoint_filter': {
            '()': IgnoreHealthCheckFilter,
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': log_file,
            'formatter': 'default',
            'encoding': 'utf-8',
            'filters': ['endpoint_filter'],
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'uvicorn': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'uvicorn.access': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'openai': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

CUDA = "cuda"
CPU = "cpu"
MPS = "mps"

def get_device():
    return CPU

class Settings(BaseSettings):
    # API Listen
    LISTEN_IP: str = "0.0.0.0"
    PORT: int = 9001

    ENV: str = "pre"
    TZ: str = "Asia/Shanghai"

    DEVICE: str = get_device()

    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    DOMAIN: str = "localhost"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    # 本地环境
    PATH:str = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    UPLOAD_ROOT_PATH:str = os.path.join(PATH, "upload")
    OUTPUT_ROOT_PATH:str = os.path.join(PATH, "output")

    MODELS_DIR:str = "models/"

    EMBEDDING_MODEL_V1: str = MODELS_DIR + "xiaobu-embedding-v2"
    TOKENIZER_MODEL: str = MODELS_DIR + "Qwen2-0.5B-Instruct-GPTQ-Int4"

    HTTP_PROXY:str = "http://127.0.0.1:7890"
    HTTP_PROXIES:dict = {
        "http": HTTP_PROXY,
        "https": HTTP_PROXY,
    }

    #汇率
    USD_TO_CNY:float = 7.2
    M:int = 1000000

    DEFAULT_TEMPERATURE:int = 1
    DEFAULT_TOP_P:int = 1
    QA_NO_RESULT_RSP:str = "非常抱歉，因为某些原因，暂时无法回答您的问题，请稍后再试或者换个问题"

    AUDIO_QUEUE_MAXSIZE:int = 300
    VERSION1:str = "1.0"

    POSTGRES_SERVER: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "qa"
    POSTGRES_USER: str = "qa_user"
    POSTGRES_PASSWORD: str = "CfzpN8uEDkFTw"

    SONG_DIR: str = os.path.join(PATH, "assets/song")


settings = Settings() 