from typing import List
from kubernetes import client, config
from prometheus_client import CollectorRegistry, Counter, Gauge
import requests
from datetime import datetime, timedelta
from ..models.metrics import ResourceMetrics
from ..config import settings

class MetricsCollector:
    def __init__(self):
        # initialize Kubernetes client
        config.load_incluster_config()
        self.k8s_client = client.CoreV1Api()
        self.prometheus_url = settings.PROMETHEUS_URL

    async def get_pod_metrics(self, namespace: str = None) -> List[ResourceMetrics]:
        metrics = []
        try:
            # Get pods in the specified namespace
            pods = self.k8s_client.list_namespaced_pod(namespace or settings.KUBERNETES_NAMESPACE)

            for pod in pods.items:
                # Query Prometheus for CPU and memory metrics
                cpu_query = f'container_cpu_usage_seconds_total{{pod="{pod.metadata.name}"}}'
                memory_query = f'container_memory_usage_bytes{{pod="{pod.metadata.name}"}}'

                cpu_usage = self._query_prometheus(cpu_query)
                memory_usage = self._query_prometheus(memory_query)

                # Get resource requests and limits from pod spec
                cpu_request = self._get_resouce_value(pod, 'requests', 'cpu')
                memory_request = self._get_resource_value(pod, 'requests', 'memory')
                cpu_limit = self._get_resource_value(pod, 'lmits', 'cpu')
                memory_limit = self._get_resource_value(pod, 'limits', 'memory')

                metrics.append(ResourceMetrics(
                    pod_name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    cpu_request=cpu_request,
                    memory_request=memory_request,
                    cpu_limit=cpu_limit,
                    memory_limit=memory_limit,
                    timestamp=datetime.now()
                ))
        except Exception as e:
            print(f"Error collecting metrics: {str(e)}")

        return metrics
    
    def _query_prometheus(self, query: str) -> float:
        response = requests.get(
            f"{self.prometheus_url}/api/v1/query",
            params={"query": query}
        )
        if response.status_code == 200:
            result = response.json()
            if result["data"]["result"]:
                return float(result["data"]["result"][0]["value"][1])
            return 0.0
        
    def _get_resource_value(self, pod, resource_type: str, resource_name: str) -> float:
        try:
            container = pod.spec.containers[0]
            resources = getattr(container.resources, resource_type, {})
            return float(resources.get(resource_name, 0))
        
        except (AttributeError, IndexError):
            return 0.0