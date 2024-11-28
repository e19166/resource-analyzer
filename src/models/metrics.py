from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class ResourceMetrics(BaseModel):
    pod_name: str
    namespace: str
    cpu_usage: float
    memory_usage: float
    cpu_request: float
    memory_request: float
    cpu_limit: float
    memory_limit: float
    timestamp: datetime

class ResourceRecommendation(BaseModel):
    pod_name: str
    namespace: str
    current_cpu_request: float
    current_memory_request: float
    recommended_cpu_request: float
    recommended_memory_request: float
    cost_impact: float
    confident_score: float