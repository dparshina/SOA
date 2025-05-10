from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POST_SERVICE_URL: str
    DATABASE_URL: str

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

