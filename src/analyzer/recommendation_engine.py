from typing import List
import pandas as pd
from ..models.metrics import ResourceRecommendation

class RecommendationEngine:
    def __init__(slef):
        self.recommendations_history = []

    async def process_recommendations(self, recommendations: List[ResourceRecommendation]) -> List[dict]:
        processed_recommendations = []

        