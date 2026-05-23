from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os


@dataclass
class Paths:
    """Rutas comunes usadas en el proyecto."""

    root: Path = Path(".")
    data_dir: Path = Path("data")
    models_dir: Path = Path("models")

    @property
    def raw_data(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_data(self) -> Path:
        return self.data_dir / "processed"

    @property
    def external_data(self) -> Path:
        return self.data_dir / "external"


def resolve_path(path: Optional[str]) -> Path:
    """Convierte una ruta opcional en `Path`."""

    return Path(path) if path else Path(".")


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Wrapper mínimo para leer variables de entorno."""

    return os.getenv(name, default)
