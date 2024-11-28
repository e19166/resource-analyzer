import pandas as pd
import numpy as np
from typing import List, Tuple
from datetime import datetime, timedelta
from ..models.metrics import ResourceMetrics, ResourceRecommendation
from ..config import settings

class ResourceAnalyzer:
    def __init__(self):
        self.cpu_threshold = settings.RESOURCE_THRESHOLD_CPU
        self.memory_threshold = settings.RESOURCE_THRESHOLD_MEMORY

    async def analyze_metrics(self, metrics: List[ResourceMetrics]) -> List[ResourceRecommendation]:
        recommendations = []
        
        # Group metrics by pod
        pod_metrics = {}
        for metric in metrics:
            if metric.pod_name not in pod_metrics:
                pod_metrics[metric.pod_name] = []
            pod_metrics[metric.pod_name].append(metric)

        for pod_name, pod_data in pod_metrics.items():
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame([m.dict() for m in pod_data])

            # Calculate resource utilization patterns
            cpu_pattern = self._analyze_resource_pattern(df['cpu_usage'], df['cpu_request'])
            memory_pattern = self._analyze_resource_pattern(df['memory_usage'], df['memory_request'])

            # Generate recommendations
            cpu_recommendation = self._generate_resource_recommendation(
                current=df['cpu_request'].iloc[-1],
                usage=df['cpu_usage'],
                pattern=cpu_pattern
            )

            memory_recommendation = self._generate_resource_recommendation(
                current=df['memory_request'].iloc[-1],
                usage=df['memory_usage'],
                pattern=memory_pattern
            )

            # Calculate potential cost impact
            cost_impact = self._calculate_cost_impact(
                current_cpu=df['cpu_request'].iloc[-1],
                recommended_cpu=cpu_recommendation,
                current_memory=df['memory_request'].iloc[-1],
                recommended_memory=memory_recommendation
            )

            # Calculate confidence score based on data quality and pattern stability
            confidence_score = self._calculate_confidence_score(df)

            recommendations.append(ResourceRecommendation(
                pod_name=pod_name,
                namespace=df['namespace'].iloc[0],
                current_cpu_request=df['cpu_request'].iloc[-1],
                current_memory_request=df['memory_request'].iloc[-1],
                recommended_cpu_request=cpu_recommendation,
                recommended_memory_request=memory_recommendation,
                cost_impact=cost_impact,
                confidence_score=confidence_score
            ))

        return recommendations

    def _analyze_resource_pattern(self, usage: pd.Series, request: pd.Series) -> dict:
        return {
            'mean': usage.mean(),
            'std': usage.std(),
            'peak': usage.max(),
            'p95': usage.quantile(0.95),
            'utilization': (usage / request).mean()
        }
    
    def _generate_resource_recommendation(self, current: float, usage: pd.Series, pattern: dict) -> float:
        if pattern['utilization'] > self.cpu_threshold:
            # High utilization: recommend based on P95 plus buffer
            recommendation = pattern['p95'] * 1.2
        elif pattern['utilization'] < 0.4:
            #Low utilization: recommend based on mean plus standard deviation
            recommendation = pattern['mean'] + pattern['std']
        else:
            # Moderate utilization: keep current allocation
            recommendation = current

        # Ensure recommendation is not less than minimum required
        return max(recommendation, usage.min() * 1.1)
    
    def _calculate_cost_impact(self, current_cpu: float, recommended_cpu: float, current_memory: float, recommended_memory: float) -> float:
        # Simplified cost calculation
        cpu_cost_per_core = 25 # Example cost per CPU core
        memory_cost_per_gb = 10 # Example cost per GB of memory

        cpu_cost_diff = (recommended_cpu - current_cpu) * cpu_cost_per_core
        memory_cost_diff = (recommended_memory - current_memory) * memory_cost_per_gb

        return cpu_cost_diff + memory_cost_diff
    
    def _calculate_confidence_score(self, df: pd.DataFrame) -> float:
        # Calculate confidence score based on:
        # 1. Amount of data available
        # 2. Stability of measurements
        # 3. Pattern predictability

        data_points = len(df)
        if data_points < 10:
            return 0.5 # Low confidence with limited data
        
        # Calculate stability score
        cpu_stability = 1 - (df['cpu_usage'].std() / df['cpu_usage'].mean())
        memory_stability = 1 - (df['memory_usage'].std() / df['memory_usage'].mean())

        # Combine score
        confidence = (cpu_stability + memory_stability) / 2

        # Normalized to 0-1 range
        return max(min(confidence, 1.0), 0.0)

        
    