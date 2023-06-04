from typing import Dict, Literal, Optional

from pydantic import BaseModel
from pydantic import FilePath
from pydantic import IPvAnyNetwork
import yaml


class NetworkConfig(BaseModel):
    mode: Literal["bridge", "nat"]
    interface: Optional[str]
    subnet: IPvAnyNetwork


class BaseImage(BaseModel):
    path: FilePath
    root_password: str


class OAuthConfig(BaseModel):
    provider: Literal["google", "github"]
    client_id: str
    client_secret: str


class Config(BaseModel):
    env: Literal["development", "production"]

    libvirt: str
    db: str

    session_secret: str
    jwt_secret: str

    oauth: OAuthConfig

    maxvcpus: int
    maxram: str

    network: NetworkConfig

    images: Dict[str, BaseImage]

    @property
    def base_url(self):
        if self.env == "development":
            return "http://localhost:5173"

        raise NotImplementedError()


def parse_config(path: str = "config.yaml"):
    with open("config.yaml", "r") as f:
        o = yaml.safe_load(f)
    return Config.parse_obj(o)


config = parse_config()