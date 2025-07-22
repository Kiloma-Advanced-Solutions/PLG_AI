"""
Health checker for monitoring system status
"""
import time
import logging
from datetime import datetime
from typing import Optional

from core.llm_engine import llm_engine
from core.models import HealthStatus

logger = logging.getLogger(__name__)

class HealthChecker:
    """Health checker with robust monitoring and error handling"""
    
    def __init__(self):
        self.engine = llm_engine
        self.start_time = time.time()
        self.last_health_check: Optional[datetime] = None
        self.consecutive_failures = 0
        self.max_failures_before_unhealthy = 3

    async def check_system_health(self) -> HealthStatus:
        """
        Comprehensive system health check with failure tracking
        
        Returns:
            HealthStatus with current system state
        """
        try:
            # Check vLLM server health
            vllm_healthy = await self.engine.check_health()
            
            # Update failure tracking
            if vllm_healthy:
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
                logger.warning(f"vLLM health check failed (consecutive failures: {self.consecutive_failures})")
            
            # Get current metrics (non-blocking)
            metrics = await self._get_safe_metrics()
            session_info = self.engine.get_session_info()
            
            # Determine overall system status
            system_healthy = (
                vllm_healthy and 
                self.consecutive_failures < self.max_failures_before_unhealthy
            )
            status = "healthy" if system_healthy else "unhealthy"
            
            # Calculate uptime
            uptime = time.time() - self.start_time
            
            # Update tracking
            self.last_health_check = datetime.now()
            
            return HealthStatus(
                status=status,
                vllm_healthy=vllm_healthy,
                active_sessions=session_info["active_sessions"],
                uptime=uptime,
                vllm_running_requests=metrics.get("running"),
                vllm_waiting_requests=metrics.get("waiting"),
                timestamp=self.last_health_check
            )
            
        except Exception as e:
            logger.error(f"Health check system error: {e}")
            self.consecutive_failures += 1
            
            return HealthStatus(
                status="unhealthy",
                vllm_healthy=False,
                active_sessions=0,
                uptime=time.time() - self.start_time,
                timestamp=datetime.now()
            )

    async def _get_safe_metrics(self) -> dict:
        """Get vLLM metrics with error handling"""
        try:
            return await self.engine.get_metrics()
        except Exception as e:
            logger.warning(f"Failed to get vLLM metrics: {e}")
            return {"running": None, "waiting": None}

# Global health checker instance
health_checker = HealthChecker() 