from pydantic import BaseSettings

class Settings(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str = None
    MAIN_API: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
