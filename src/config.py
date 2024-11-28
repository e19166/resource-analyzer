from pydantic import BaseSettings

class Settings(BaseSettings):
    PROMETHEUS_URL: str = "http://prometheus-server:9090"
    KUBERNETES_NAMESPACE: str = "default"
    ANALYSIS_INTERVAL_MINUTES: int = 15
    RESOURCE_THRESHOLD_CPU: float = 0.8
    RESOURCE_THRESHOLD_MEMORY: float = 0.8

    class Config:
        env_file = ".env"

settings = Settings()