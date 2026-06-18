from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    storage_root: str = Field("./storage", env="STORAGE_ROOT")
    data_root: str = Field("./data", env="DATA_ROOT")
    forge_ingest_api_key: str = Field(..., env="FORGE_INGEST_API_KEY")
    lens_public_access: bool = Field(True, env="LENS_PUBLIC_ACCESS")
    storage_secret : str = Field(..., env="STORAGE_SECRET")
    

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()