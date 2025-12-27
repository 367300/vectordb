from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .constants import DistanceMetric, IndexAlgorithm

# Загружаем переменные из .env файла
load_dotenv()


@dataclass
class Settings:
    """Application configuration settings."""

    environment: str = field(default_factory=lambda: os.getenv("ENV", "local"))
    data_dir: Path = field(
        default_factory=lambda: Path(os.getenv("DATA_DIR", "data")).resolve()
    )
    cohere_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("COHERE_API_KEY")
    )
    # WARNING: Set your secret key either in the environment variable or in the .env file,
    # otherwise it will be randomly generated and you will not be able to access the service!
    jwt_secret_key: str = field(
        default_factory=lambda: os.getenv("JWT_SECRET_KEY") or os.urandom(32).hex()
    )
    # Ключ для шифрования токенов перед передачей пользователю
    encryption_key: str = field(
        default_factory=lambda: os.getenv("ENCRYPTION_KEY") or os.getenv("JWT_SECRET_KEY") or os.urandom(32).hex()
    )
    default_metric: str = field(
        default_factory=lambda: os.getenv("DEFAULT_METRIC", DistanceMetric.COSINE.value)
    )
    default_index: str = field(
        default_factory=lambda: os.getenv("DEFAULT_INDEX", IndexAlgorithm.LINEAR.value)
    )

    # LSH configuration
    lsh_num_planes: int = field(
        default_factory=lambda: int(os.getenv("LSH_NUM_PLANES", "16"))
    )
    lsh_num_tables: int = field(
        default_factory=lambda: int(os.getenv("LSH_NUM_TABLES", "4"))
    )
    lsh_seed: int = field(default_factory=lambda: int(os.getenv("LSH_SEED", "42")))

    # Logging configuration
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def __post_init__(self) -> None:
        """Post-initialization to create directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
