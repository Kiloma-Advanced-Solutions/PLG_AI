#!/usr/bin/env python3
"""
Multi-User LLM Performance Simulation
Tests concurrent inference with multiple users using vLLM metrics for visualization
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from transformers import AutoTokenizer
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class RequestMetrics:
    """Metrics for a single request using vLLM native metrics"""
    user_id: int
    request_id: int
    prompt: str
    context_length: int  # tokens in prompt (from tokenizer)
    start_time: float
    end_time: Optional[float] = None
    # vLLM metrics snapshots
    vllm_metrics_start: Dict[str, float] = field(default_factory=dict)
    vllm_metrics_end: Dict[str, float] = field(default_factory=dict)
    # Derived metrics from vLLM data
    ttft: Optional[float] = None  # Time to first token (from vLLM metrics)
    tokens_per_second: Optional[float] = None  # From vLLM metrics
    total_context_at_start: Optional[int] = None  # Total context of all users
    error: Optional[str] = None

@dataclass
class UserState:
    """State for a single simulated user"""
    user_id: int
    session_id: str
    conversation: List[Dict[str, str]] = field(default_factory=list)
    request_count: int = 0
    active: bool = True
    empty_response_count: int = 0

@dataclass
class SystemSnapshot:
    """System-wide metrics snapshot from vLLM"""
    timestamp: float
    running_requests: int = 0
    waiting_requests: int = 0
    gpu_cache_usage: float = 0.0
    kv_cache_usage: float = 0.0
    total_generation_tokens: float = 0.0
    ttft_sum: float = 0.0
    ttft_count: float = 0.0
    time_per_token_sum: float = 0.0
    time_per_token_count: float = 0.0

class MultiUserSimulation:
    """Multi-user simulation with vLLM metrics integration"""
    
    def __init__(self, api_url: str = "http://localhost:8090", 
                 model_name: str = "gaunernst/gemma-3-12b-it-qat-autoawq",
                 num_users: int = 5):
        self.api_url = api_url
        self.model_name = model_name
        self.chat_endpoint = f"{api_url}/api/chat/stream"
        self.health_endpoint = f"{api_url}/api/health"
        self.vllm_metrics_url = "http://localhost:8060/metrics"  # vLLM server metrics
        
        # Simulation configuration
        self.num_users = num_users
        self.user_start_delay = 5.0  # 5 seconds between user starts
        self.request_delay = 10.0    # 10 seconds between requests per user
        
        # Initialize tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            logger.info(f"Loaded tokenizer for {model_name}")
        except Exception as e:
            logger.warning(f"Could not load tokenizer for {model_name}: {e}")
        
        # Data storage
        self.request_metrics: List[RequestMetrics] = []
        self.system_snapshots: List[SystemSnapshot] = []
        self.users: List[UserState] = []
        
        # Monitoring control
        self.monitoring_active = False
        self.simulation_start_time = 0.0
        
        # Test prompts with increasing complexity (15 prompts total)
        self.prompts = [
            "שלום, איך אתה?",
            "תוכל לספר לי על ההיסטוריה של ישראל?",
            "אני רוצה לדעת על הטכנולוגיה החדשה בתחום הבינה המלאכותית. תוכל להסביר לי על מודלי שפה גדולים ואיך הם עובדים?",
            "בואו נדבר על פיתוח תוכנה. אני מעוניין לדעת על ארכיטקטורות מיקרו-שירותים, איך לעצב מערכות מבוזרות, ומה הן השיטות הטובות ביותר לניהול מסדי נתונים בסביבות ענן.",
            "אני חוקר את התחום של למידת מכונה ובינה מלאכותית. תוכל להסביר לי על האלגוריתמים השונים כמו רשתות נוירונים, עצי החלטה, SVM, ואיך הם משתלבים במערכות ייצור? גם אשמח לדעת על אתגרים בעיבוד נתונים גדולים.",
            "מה דעתך על השפעת הבינה המלאכותית על שוק העבודה? איך אנשים יכולים להתכונן לעתיד שבו AI יהיה חלק מרכזי מהכלכלה?",
            "תוכל להסביר לי על אבטחת מידע וסייבר? מה הן האיומים העיקריים היום ואיך ארגונים יכולים להגן על עצמם?",
            "אני מעוניין ללמוד על פיזיקה קוונטית. תוכל להסביר לי את העקרונות הבסיסיים ואת הקשר למחשוב קוונטי?",
            "בואו נדבר על שינויי אקלים. מה הן הסיבות העיקריות ומה אפשר לעשות כדי להילחם בבעיה הזו?",
            "תוכל לספר לי על הפילוסופיה של אריסטו ואיך היא משפיעה על החשיבה המודרנית?",
            "אני רוצה להבין את הכלכלה הגלובלית. איך עובדים שווקים פיננסיים בינלאומיים ומה משפיע על שערי החליפין?",
            "מה אתה יודע על רפואה מותאמת אישית וגנומיקה? איך הטכנולוגיות האלה משנות את הטיפול הרפואי?",
            "תוכל להסביר לי על תיאוריית היחסות של איינשטיין ואת ההשלכות שלה על הבנתנו את היקום?",
            "אני מעוניין ללמוד על פסיכולוגיה קוגניטיבית. איך המוח מעבד מידע ומה אנחנו יודעים על זיכרון ולמידה?",
            "בואו נדבר על עתיד הטכנולוגיה. מה הטרנדים החשובים ביותר שאתה רואה בעשור הקרוב - בתחומי AI, ביוטכנולוגיה, אנרגיה מתחדשת וחקר החלל?"
        ]
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using the model's tokenizer"""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
    
    def count_conversation_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in a conversation using the model's chat template"""
        try:
            # Use the tokenizer's chat template for accurate token counting
            if hasattr(self.tokenizer, 'apply_chat_template'):
                formatted_text = self.tokenizer.apply_chat_template(
                    messages, 
                    tokenize=False, 
                    add_generation_prompt=True
                )
                return len(self.tokenizer.encode(formatted_text))
            else:
                # Fallback: manually format and count
                formatted_text = ""
                for msg in messages:
                    formatted_text += f"<|{msg['role']}|>\n{msg['content']}\n"
                return len(self.tokenizer.encode(formatted_text))
        except Exception as e:
            logger.debug(f"Chat template failed ({e}), using fallback counting")
            # Fallback to simple counting - more reliable
            total_text = " ".join([msg['content'] for msg in messages])
            return self.count_tokens(total_text)
    
    async def check_api_health(self) -> bool:
        """Check if the API is healthy and ready"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.health_endpoint, timeout=5) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        logger.info(f"API Health: {health_data}")
                        return health_data.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        return False
    
    async def get_vllm_metrics(self) -> Dict[str, float]:
        """Get vLLM metrics from the metrics endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.vllm_metrics_url, timeout=2) as response:
                    if response.status == 200:
                        metrics_text = await response.text()
                        
                        metrics = {}
                        
                        # Parse vLLM metrics
                        for line in metrics_text.split('\n'):
                            if line.startswith('#') or not line.strip():
                                continue
                            
                            parts = line.split()
                            if len(parts) < 2:
                                continue
                            
                            # Extract metric name (before any labels)
                            metric_full = parts[0]
                            metric_name = metric_full.split('{')[0]  # Remove labels
                            try:
                                metric_value = float(parts[-1])
                            except (ValueError, IndexError):
                                continue  # Skip invalid metric values
                            
                            # Collect relevant metrics
                            if metric_name == "vllm:num_requests_running":
                                metrics['num_requests_running'] = int(metric_value)
                            elif metric_name == "vllm:num_requests_waiting":
                                metrics['num_requests_waiting'] = int(metric_value)
                            elif metric_name == "vllm:gpu_cache_usage_perc":
                                metrics['gpu_cache_usage_perc'] = metric_value
                            elif metric_name == "vllm:kv_cache_usage_perc":
                                metrics['kv_cache_usage_perc'] = metric_value
                            elif metric_name == "vllm:generation_tokens_total":
                                metrics['generation_tokens_total'] = metric_value
                            elif metric_name == "vllm:time_to_first_token_seconds_sum":
                                metrics['ttft_sum'] = metric_value
                            elif metric_name == "vllm:time_to_first_token_seconds_count":
                                metrics['ttft_count'] = metric_value
                            elif metric_name == "vllm:time_per_output_token_seconds_sum":
                                metrics['time_per_output_token_sum'] = metric_value
                            elif metric_name == "vllm:time_per_output_token_seconds_count":
                                metrics['time_per_output_token_count'] = metric_value
                        
                        return metrics
        except Exception as e:
            logger.debug(f"Failed to get vLLM metrics: {e}")
        return {}
    
    def calculate_total_context_length(self) -> int:
        """Calculate the total context length of all active users"""
        total_context = 0
        for user in self.users:
            if user.conversation:
                total_context += self.count_conversation_tokens(user.conversation)
        return total_context
    
    def calculate_ttft_from_vllm_metrics(self, start_metrics: Dict, end_metrics: Dict) -> Optional[float]:
        """Calculate average TTFT from vLLM metrics difference"""
        try:
            start_sum = start_metrics.get('ttft_sum', 0)
            end_sum = end_metrics.get('ttft_sum', 0)
            start_count = start_metrics.get('ttft_count', 0)
            end_count = end_metrics.get('ttft_count', 0)
            
            sum_diff = end_sum - start_sum
            count_diff = end_count - start_count
            
            if count_diff > 0 and sum_diff > 0:
                return sum_diff / count_diff
        except Exception as e:
            logger.debug(f"TTFT calculation failed: {e}")
        return None
    
    def calculate_tokens_per_second_from_vllm_metrics(self, start_metrics: Dict, end_metrics: Dict) -> Optional[float]:
        """Calculate tokens per second from vLLM metrics difference"""
        try:
            start_sum = start_metrics.get('time_per_output_token_sum', 0)
            end_sum = end_metrics.get('time_per_output_token_sum', 0)
            start_count = start_metrics.get('time_per_output_token_count', 0)
            end_count = end_metrics.get('time_per_output_token_count', 0)
            
            sum_diff = end_sum - start_sum
            count_diff = end_count - start_count
            
            if count_diff > 0 and sum_diff > 0:
                avg_time_per_token = sum_diff / count_diff
                return 1.0 / avg_time_per_token
        except Exception as e:
            logger.debug(f"Tokens per second calculation failed: {e}")
        return None
    
    async def system_metrics_monitor(self):
        """Continuously monitor system metrics during simulation"""
        self.monitoring_active = True
        logger.info("Starting system metrics monitoring")
        
        while self.monitoring_active:
            try:
                current_time = time.time()
                metrics = await self.get_vllm_metrics()
                
                snapshot = SystemSnapshot(
                    timestamp=current_time - self.simulation_start_time,
                    running_requests=metrics.get('num_requests_running', 0),
                    waiting_requests=metrics.get('num_requests_waiting', 0),
                    gpu_cache_usage=metrics.get('gpu_cache_usage_perc', 0.0),
                    kv_cache_usage=metrics.get('kv_cache_usage_perc', 0.0),
                    total_generation_tokens=metrics.get('generation_tokens_total', 0.0),
                    ttft_sum=metrics.get('ttft_sum', 0.0),
                    ttft_count=metrics.get('ttft_count', 0.0),
                    time_per_token_sum=metrics.get('time_per_output_token_sum', 0.0),
                    time_per_token_count=metrics.get('time_per_output_token_count', 0.0)
                )
                
                self.system_snapshots.append(snapshot)
                
                # Log every 10 seconds
                if len(self.system_snapshots) % 5 == 0:  # Every 5 snapshots (10 seconds)
                    logger.info(f"System state: {snapshot.running_requests} running, "
                              f"{snapshot.waiting_requests} waiting, "
                              f"GPU cache: {snapshot.gpu_cache_usage:.1f}%")
                
                await asyncio.sleep(2)  # Monitor every 2 seconds
                
            except Exception as e:
                logger.debug(f"Metrics monitoring error: {e}")
                await asyncio.sleep(2)
        
        logger.info("System metrics monitoring stopped")
    
    async def send_chat_request(self, user: UserState, prompt: str) -> RequestMetrics:
        """Send a single chat request and capture metrics"""
        request_id = user.request_count
        user.request_count += 1
        
        # Prepare conversation with new user message (but don't add to user.conversation yet)
        temp_conversation = user.conversation.copy()
        temp_conversation.append({"role": "user", "content": prompt})
        
        # Count tokens in the full conversation context
        context_tokens = self.count_conversation_tokens(temp_conversation)
        total_context = self.calculate_total_context_length()
        
        logger.info(f"User {user.user_id} starting request {request_id+1} "
                   f"(context: {context_tokens} tokens, total: {total_context} tokens)")
        
        # Create metrics object
        start_time = time.time()
        metrics = RequestMetrics(
            user_id=user.user_id,
            request_id=request_id,
            prompt=prompt,
            context_length=context_tokens,
            start_time=start_time,
            total_context_at_start=total_context
        )
        
        # Get vLLM metrics before starting request
        metrics.vllm_metrics_start = await self.get_vllm_metrics()
        
        # Prepare request payload using the temporary conversation
        payload = {
            "messages": temp_conversation,
            "session_id": user.session_id,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 512
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=1200)  # 20 minute timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.chat_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status != 200:
                        metrics.error = f"HTTP {response.status}"
                        metrics.end_time = time.time()
                        return metrics
                    
                    # Process streaming response
                    assistant_response = ""
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        
                        if line_str.startswith("data: "):
                            data_str = line_str[6:]  # Remove "data: " prefix
                            
                            if data_str == "[DONE]":
                                logger.info(f"User {user.user_id} request {request_id+1} completed")
                                break
                            
                            try:
                                data = json.loads(data_str)
                                
                                # Handle different streaming response formats
                                content = None
                                
                                # Format 1: Direct content field
                                if "content" in data:
                                    content = data["content"]
                                
                                # Format 2: OpenAI-style streaming with choices
                                elif "choices" in data and len(data["choices"]) > 0:
                                    choice = data["choices"][0]
                                    if "delta" in choice and "content" in choice["delta"]:
                                        content = choice["delta"]["content"]
                                    elif "text" in choice:
                                        content = choice["text"]
                                
                                # Format 3: Simple text field
                                elif "text" in data:
                                    content = data["text"]
                                
                                # Accumulate content
                                if content:
                                    assistant_response += content
                                    
                            except json.JSONDecodeError:
                                # Skip malformed JSON lines
                                continue
                    
                    # Add both user message and assistant response to conversation on success
                    if assistant_response:
                        # Success: Add both user message and assistant response
                        user.conversation.append({"role": "user", "content": prompt})
                        user.conversation.append({"role": "assistant", "content": assistant_response})
                        user.empty_response_count = 0  # Reset counter on successful response
                        logger.info(f"User {user.user_id} request {request_id+1} completed: {len(assistant_response)} chars")
                    else:
                        # Empty response - this shouldn't happen with vLLM queuing
                        # But if it does, it indicates a real problem (timeout, connection error, etc.)
                        user.empty_response_count += 1
                        logger.error(f"User {user.user_id} request {request_id+1} failed - no response received (attempt #{user.empty_response_count})")
                        
                        # Don't add anything to conversation - this request failed completely
                        # The conversation should not include failed requests
                        
                        # Stop user only after multiple consecutive failures (real system issues)
                        if user.empty_response_count >= 5:
                            user.active = False
                            logger.error(f"User {user.user_id} stopped due to {user.empty_response_count} consecutive failures - system may be down")
                    
                    # Record end time and get final metrics
                    metrics.end_time = time.time()
                    metrics.vllm_metrics_end = await self.get_vllm_metrics()
                    
                    # Calculate derived metrics from vLLM data
                    metrics.ttft = self.calculate_ttft_from_vllm_metrics(
                        metrics.vllm_metrics_start, metrics.vllm_metrics_end)
                    metrics.tokens_per_second = self.calculate_tokens_per_second_from_vllm_metrics(
                        metrics.vllm_metrics_start, metrics.vllm_metrics_end)
                        
        except Exception as e:
            metrics.error = str(e)
            metrics.end_time = time.time()
            # Still try to get end metrics even on error
            metrics.vllm_metrics_end = await self.get_vllm_metrics()
            
            # Track consecutive failures
            user.empty_response_count += 1
            logger.error(f"Request failed for user {user.user_id}: {e} (failure #{user.empty_response_count})")
            
            # Don't add anything to conversation on exception
            # Stop user after multiple consecutive failures
            if user.empty_response_count >= 5:
                user.active = False
                logger.error(f"User {user.user_id} stopped due to {user.empty_response_count} consecutive failures")
        
        return metrics
    
    async def simulate_user(self, user_id: int, start_delay: float):
        """Simulate a single user's behavior"""
        # Wait for start delay
        await asyncio.sleep(start_delay)
        
        user = UserState(
            user_id=user_id,
            session_id=f"sim_user_{user_id}_{int(time.time())}"
        )
        self.users.append(user)
        
        logger.info(f"User {user_id} starting simulation")
        
        # Send requests with increasing complexity
        for i, prompt in enumerate(self.prompts):
            if not user.active:
                break
                
            logger.info(f"User {user_id} sending request {i+1}: {prompt[:50]}...")
            
            # Send request and collect metrics
            metrics = await self.send_chat_request(user, prompt)
            self.request_metrics.append(metrics)
            
            # Log metrics
            if metrics.error:
                logger.error(f"User {user_id} request {i+1} failed: {metrics.error}")
            else:
                logger.info(f"User {user_id} request {i+1} completed: "
                           f"Context={metrics.context_length} tokens, "
                           f"TTFT={metrics.ttft:.3f}s" if metrics.ttft else "TTFT=N/A")
            
            # Wait before next request (except for last request)
            if i < len(self.prompts) - 1:
                await asyncio.sleep(self.request_delay)
        
        user.active = False
        logger.info(f"User {user_id} completed simulation")
    
    async def run_simulation(self):
        """Run the complete multi-user simulation"""
        logger.info("Starting multi-user simulation...")
        
        # Check API health
        if not await self.check_api_health():
            logger.error("API is not healthy. Aborting simulation.")
            return
        
        # Record simulation start time
        self.simulation_start_time = time.time()
        
        # Start system metrics monitoring
        monitor_task = asyncio.create_task(self.system_metrics_monitor())
        
        # Start all users with delays
        tasks = []
        for user_id in range(self.num_users):
            start_delay = user_id * self.user_start_delay
            task = asyncio.create_task(self.simulate_user(user_id, start_delay))
            tasks.append(task)
        
        # Wait for all users to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop monitoring
        self.monitoring_active = False
        monitor_task.cancel()
        
        # Log empty response summary
        users_with_failures = [user for user in self.users if user.empty_response_count > 0]
        if users_with_failures:
            logger.warning(f"Empty response summary:")
            for user in users_with_failures:
                logger.warning(f"  User {user.user_id}: {user.empty_response_count} empty responses")
            total_empty = sum(user.empty_response_count for user in users_with_failures)
            logger.warning(f"  Total empty responses: {total_empty}")
        else:
            logger.info("No empty responses detected - all requests successful!")
        
        logger.info("Multi-user simulation completed")
    
    def generate_graphs(self):
        """Generate the five performance graphs using vLLM metrics"""
        if not self.request_metrics:
            logger.error("No request metrics collected")
            return
        
        # Filter successful requests
        successful_requests = [m for m in self.request_metrics if not m.error]
        if not successful_requests:
            logger.error("No successful requests to analyze")
            return
        
        # Create figure with 5 subplots (3x2 grid, one subplot empty)
        fig, axes = plt.subplots(3, 2, figsize=(16, 18))
        fig.suptitle('RTX PRO 6000 WS Simulation\nMulti-User LLM Performance Results', fontsize=18, fontweight='bold')
        
        # 1. Time to First Token - Line Chart (one line per user)
        ax1 = axes[0, 0]
        user_ttft_data = defaultdict(list)
        user_request_ids = defaultdict(list)
        
        for req in successful_requests:
            if req.ttft is not None:
                user_ttft_data[req.user_id].append(req.ttft)
                user_request_ids[req.user_id].append(req.request_id + 1)  # 1-indexed
        
        for user_id in sorted(user_ttft_data.keys()):
            ax1.plot(user_request_ids[user_id], user_ttft_data[user_id], 
                    marker='o', label=f'User {user_id}', linewidth=2, markersize=6)
        
        ax1.set_xlabel('Request Number')
        ax1.set_ylabel('Time to First Token (seconds)')
        ax1.set_title('Time to First Token per User')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Token Generation Speed - Line Chart (one line per user)
        ax2 = axes[0, 1]
        user_tps_data = defaultdict(list)
        user_tps_request_ids = defaultdict(list)
        
        for req in successful_requests:
            if req.tokens_per_second is not None:
                user_tps_data[req.user_id].append(req.tokens_per_second)
                user_tps_request_ids[req.user_id].append(req.request_id + 1)  # 1-indexed
        
        for user_id in sorted(user_tps_data.keys()):
            ax2.plot(user_tps_request_ids[user_id], user_tps_data[user_id], 
                    marker='s', label=f'User {user_id}', linewidth=2, markersize=6)
        
        ax2.set_xlabel('Request Number')
        ax2.set_ylabel('Token Generation Speed (tokens/sec)')
        ax2.set_title('Token Generation Speed per User')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Request Status - Line Chart (running vs waiting requests)
        ax3 = axes[1, 0]
        if self.system_snapshots:
            timestamps = [s.timestamp for s in self.system_snapshots]
            running_requests = [s.running_requests for s in self.system_snapshots]
            waiting_requests = [s.waiting_requests for s in self.system_snapshots]
            
            ax3.plot(timestamps, running_requests, 
                    marker='o', label='Running Requests', linewidth=2, markersize=4, color='green')
            ax3.plot(timestamps, waiting_requests, 
                    marker='s', label='Waiting Requests', linewidth=2, markersize=4, color='red')
            
            ax3.set_xlabel('Time (seconds)')
            ax3.set_ylabel('Number of Requests')
            ax3.set_title('Request Status Over Time')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        else:
            ax3.text(0.5, 0.5, 'No system snapshots available', 
                    ha='center', va='center', transform=ax3.transAxes,
                    fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            ax3.set_title('Request Status Over Time\n(Data unavailable)')
        
        # 4. Token Generation Speed (total) vs Total Context Length
        ax4 = axes[1, 1]
        context_lengths = []
        token_speeds = []
        
        for req in successful_requests:
            if req.tokens_per_second is not None and req.total_context_at_start is not None:
                context_lengths.append(req.total_context_at_start)
                token_speeds.append(req.tokens_per_second)
        
        if context_lengths and token_speeds:
            ax4.scatter(context_lengths, token_speeds, 
                       alpha=0.7, s=50, color='darkblue')
            
            # Add trend line
            if len(context_lengths) > 1:
                z = np.polyfit(context_lengths, token_speeds, 1)
                p = np.poly1d(z)
                ax4.plot(sorted(context_lengths), p(sorted(context_lengths)), 
                        "r--", alpha=0.8, linewidth=2, label='Trend')
                ax4.legend()
            
            ax4.set_xlabel('Total Context Length (tokens)')
            ax4.set_ylabel('Token Generation Speed (tokens/sec)')
            ax4.set_title('Token Generation Speed vs Total Context Length')
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'No token speed vs context data available', 
                    ha='center', va='center', transform=ax4.transAxes,
                    fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            ax4.set_title('Token Generation Speed vs Total Context Length\n(Data unavailable)')
        
        # 5. Request Status vs Total Context Length
        ax5 = axes[2, 0]
        
        # Collect data points where we have both system snapshots and context information
        context_running_data = []
        context_waiting_data = []
        context_total_data = []
        
        # Create a mapping of timestamps to total context lengths from successful requests
        timestamp_to_context = {}
        for req in successful_requests:
            if req.total_context_at_start is not None:
                # Approximate timestamp based on user start delay and request timing
                approx_timestamp = req.user_id * self.user_start_delay + req.request_id * self.request_delay
                timestamp_to_context[approx_timestamp] = req.total_context_at_start
        
        # Match system snapshots with context data
        for snapshot in self.system_snapshots:
            # Find the closest context measurement to this timestamp
            closest_context = None
            min_time_diff = float('inf')
            
            for req_timestamp, context_length in timestamp_to_context.items():
                time_diff = abs(snapshot.timestamp - req_timestamp)
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_context = context_length
            
            # Only include if we found a reasonably close context measurement (within 30 seconds)
            if closest_context is not None and min_time_diff < 30:
                context_running_data.append((closest_context, snapshot.running_requests))
                context_waiting_data.append((closest_context, snapshot.waiting_requests))
                context_total_data.append((closest_context, snapshot.running_requests + snapshot.waiting_requests))
        
        if context_running_data and context_waiting_data:
            # Sort by context length for better visualization
            context_running_data.sort(key=lambda x: x[0])
            context_waiting_data.sort(key=lambda x: x[0])
            context_total_data.sort(key=lambda x: x[0])
            
            # Extract context lengths and request counts
            running_contexts = [x[0] for x in context_running_data]
            running_counts = [x[1] for x in context_running_data]
            waiting_contexts = [x[0] for x in context_waiting_data]
            waiting_counts = [x[1] for x in context_waiting_data]
            total_contexts = [x[0] for x in context_total_data]
            total_counts = [x[1] for x in context_total_data]
            
            # Create scatter plots
            ax5.scatter(running_contexts, running_counts, 
                       alpha=0.7, s=30, color='green', label='Running Requests')
            ax5.scatter(waiting_contexts, waiting_counts, 
                       alpha=0.7, s=30, color='red', label='Waiting Requests')
            ax5.scatter(total_contexts, total_counts, 
                       alpha=0.5, s=20, color='blue', label='Total Requests')
            
            # Add trend lines if we have enough data points
            if len(total_contexts) > 2:
                try:
                    z_total = np.polyfit(total_contexts, total_counts, 1)
                    p_total = np.poly1d(z_total)
                    ax5.plot(sorted(total_contexts), p_total(sorted(total_contexts)), 
                            "b--", alpha=0.8, linewidth=2, label='Total Trend')
                except np.RankWarning:
                    pass  # Skip trend line if data is not suitable for fitting
            
            ax5.set_xlabel('Total Context Length (tokens)')
            ax5.set_ylabel('Number of Requests')
            ax5.set_title('Request Status vs Total Context Length')
            ax5.legend()
            ax5.grid(True, alpha=0.3)
        else:
            ax5.text(0.5, 0.5, 'No request status vs context data available', 
                    ha='center', va='center', transform=ax5.transAxes,
                    fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            ax5.set_title('Request Status vs Total Context Length\n(Data unavailable)')
        
        # Hide the empty subplot
        axes[2, 1].set_visible(False)
        
        plt.tight_layout()
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_path = f"simulation_results_{timestamp}.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        logger.info(f"Simulation graphs saved to {plot_path}")
        
        # Print summary
        self.print_summary(successful_requests)
        
        # Save detailed data
        self.save_detailed_data(timestamp)
        
        return plot_path
    
    def print_summary(self, successful_requests: List[RequestMetrics]):
        """Print detailed simulation summary"""
        print("\n" + "="*80)
        print("MULTI-USER SIMULATION SUMMARY")
        print("="*80)
        
        print(f"\nSimulation Configuration:")
        print(f"  - Number of users: {self.num_users}")
        print(f"  - User start delay: {self.user_start_delay}s")
        print(f"  - Request delay: {self.request_delay}s")
        print(f"  - Model: {self.model_name}")
        
        print(f"\nOverall Statistics:")
        print(f"  - Total requests: {len(self.request_metrics)}")
        print(f"  - Successful requests: {len(successful_requests)}")
        print(f"  - Failed requests: {len(self.request_metrics) - len(successful_requests)}")
        print(f"  - System snapshots collected: {len(self.system_snapshots)}")
        
        # Empty response analysis
        users_with_failures = [user for user in self.users if user.empty_response_count > 0]
        if users_with_failures:
            total_empty = sum(user.empty_response_count for user in users_with_failures)
            print(f"\nEmpty Response Analysis:")
            print(f"  - Users with empty responses: {len(users_with_failures)}/{len(self.users)}")
            print(f"  - Total empty responses: {total_empty}")
            print(f"  - Empty response rate: {(total_empty / len(self.request_metrics) * 100):.1f}%")
            for user in users_with_failures:
                print(f"    * User {user.user_id}: {user.empty_response_count} empty responses")
        else:
            print(f"\nEmpty Response Analysis:")
            print(f"  - No empty responses detected! 🎉")
        
        if successful_requests:
            # TTFT analysis
            ttft_values = [req.ttft for req in successful_requests if req.ttft is not None]
            if ttft_values:
                print(f"\nTime to First Token Analysis:")
                print(f"  - Mean TTFT: {np.mean(ttft_values):.3f}s")
                print(f"  - Median TTFT: {np.median(ttft_values):.3f}s")
                print(f"  - Min TTFT: {np.min(ttft_values):.3f}s")
                print(f"  - Max TTFT: {np.max(ttft_values):.3f}s")
                print(f"  - Data points: {len(ttft_values)}/{len(successful_requests)}")
            
            # Token generation speed analysis
            tps_values = [req.tokens_per_second for req in successful_requests if req.tokens_per_second is not None]
            if tps_values:
                print(f"\nToken Generation Speed Analysis:")
                print(f"  - Mean TPS: {np.mean(tps_values):.1f} tokens/s")
                print(f"  - Median TPS: {np.median(tps_values):.1f} tokens/s")
                print(f"  - Min TPS: {np.min(tps_values):.1f} tokens/s")
                print(f"  - Max TPS: {np.max(tps_values):.1f} tokens/s")
                print(f"  - Data points: {len(tps_values)}/{len(successful_requests)}")
            
            # Context analysis
            context_lengths = [req.context_length for req in successful_requests]
            total_contexts = [req.total_context_at_start for req in successful_requests if req.total_context_at_start is not None]
            
            print(f"\nContext Analysis:")
            print(f"  - Individual context range: {min(context_lengths)} - {max(context_lengths)} tokens")
            print(f"  - Mean individual context: {np.mean(context_lengths):.0f} tokens")
            if total_contexts:
                print(f"  - Total context range: {min(total_contexts)} - {max(total_contexts)} tokens")
                print(f"  - Mean total context: {np.mean(total_contexts):.0f} tokens")
        
        # System metrics analysis
        if self.system_snapshots:
            running_requests = [s.running_requests for s in self.system_snapshots]
            waiting_requests = [s.waiting_requests for s in self.system_snapshots]
            gpu_cache_usage = [s.gpu_cache_usage for s in self.system_snapshots]
            
            print(f"\nSystem Metrics Analysis:")
            print(f"  - Max concurrent running requests: {max(running_requests)}")
            print(f"  - Max waiting requests: {max(waiting_requests)}")
            print(f"  - Mean running requests: {np.mean(running_requests):.1f}")
            print(f"  - Mean waiting requests: {np.mean(waiting_requests):.1f}")
            if any(gpu_cache_usage):
                print(f"  - GPU cache usage range: {min(gpu_cache_usage):.1f}% - {max(gpu_cache_usage):.1f}%")
        
        print("="*80)
    
    def save_detailed_data(self, timestamp: str):
        """Save detailed metrics to CSV files"""
        # Save request metrics
        request_data = []
        for req in self.request_metrics:
            request_data.append({
                'user_id': req.user_id,
                'request_id': req.request_id,
                'context_length': req.context_length,
                'total_context_at_start': req.total_context_at_start,
                'start_time': req.start_time,
                'end_time': req.end_time,
                'duration': req.end_time - req.start_time if req.end_time else None,
                'ttft': req.ttft,
                'tokens_per_second': req.tokens_per_second,
                'error': req.error,
                'prompt_preview': req.prompt[:50] + "..." if len(req.prompt) > 50 else req.prompt
            })
        
        request_df = pd.DataFrame(request_data)
        request_csv_path = f"simulation_requests_{timestamp}.csv"
        request_df.to_csv(request_csv_path, index=False)
        logger.info(f"Request metrics saved to {request_csv_path}")
        
        # Save system snapshots
        if self.system_snapshots:
            system_data = []
            for snapshot in self.system_snapshots:
                system_data.append({
                    'timestamp': snapshot.timestamp,
                    'running_requests': snapshot.running_requests,
                    'waiting_requests': snapshot.waiting_requests,
                    'gpu_cache_usage': snapshot.gpu_cache_usage,
                    'kv_cache_usage': snapshot.kv_cache_usage,
                    'total_generation_tokens': snapshot.total_generation_tokens,
                    'ttft_sum': snapshot.ttft_sum,
                    'ttft_count': snapshot.ttft_count,
                    'time_per_token_sum': snapshot.time_per_token_sum,
                    'time_per_token_count': snapshot.time_per_token_count
                })
            
            system_df = pd.DataFrame(system_data)
            system_csv_path = f"simulation_system_{timestamp}.csv"
            system_df.to_csv(system_csv_path, index=False)
            logger.info(f"System metrics saved to {system_csv_path}")

async def main():
    """Main function to run the simulation"""
    # Configuration
    api_url = "http://localhost:8090"  # Change to your API URL
    model_name = "gaunernst/gemma-3-12b-it-qat-autoawq"  # Your model name
    num_users = 10  # Number of concurrent users
    
    simulation = MultiUserSimulation(api_url, model_name, num_users)
    
    try:
        await simulation.run_simulation()
        simulation.generate_graphs()
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
        simulation.monitoring_active = False
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        simulation.monitoring_active = False

if __name__ == "__main__":
    asyncio.run(main())
