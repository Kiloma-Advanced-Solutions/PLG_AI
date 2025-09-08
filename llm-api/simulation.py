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

# Configure logging with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m'  # Magenta
    }
    RESET = '\033[0m'  # Reset color
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

# Set up colored logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add colored formatter to console handler
for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))

# Also set up colored formatter for root logger to catch all simulation logs
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))

@dataclass
class RequestMetrics:
    """Metrics for a single request using direct client-side timing"""
    user_id: int
    request_id: int
    prompt: str
    context_length: int  # tokens in prompt (from tokenizer)
    start_time: float
    end_time: Optional[float] = None
    # Direct timing measurements (like inference_simulation.py)
    first_token_time: Optional[float] = None  # When first token arrived
    queue_time: Optional[float] = None  # Time from request sent to first token
    generation_time: Optional[float] = None  # Time from first token to completion
    ttft: Optional[float] = None  # Time to first token (queue_time)
    tokens_per_second: Optional[float] = None  # response_tokens / generation_time
    response_tokens: int = 0  # Number of tokens in response
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
    gpu_cache_usage: float = 0.0  # Only used for summary statistics

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
        self.request_delay = 5.0    # 5 seconds between requests per user
        self.instance_model = "rtx_6000"  # Instance identifier for file naming
        
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
        
        # Test prompts with increasing complexity (45 prompts total)
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
            "בואו נדבר על עתיד הטכנולוגיה. מה הטרנדים החשובים ביותר שאתה רואה בעשור הקרוב - בתחומי AI, ביוטכנולוגיה, אנרגיה מתחדשת וחקר החלל?",
            "תוכל להסביר לי על בלוקצ'יין ומטבעות דיגיטליים? איך הטכנולוגיה הזו עובדת ומה היתרונות והחסרונות של השימוש בה?",
            "אני רוצה ללמוד על ביולוגיה מולקולרית. איך עובדת שכפול DNA ומה התפקיד של RNA בתא?",
            "מה אתה יודע על אסטרונומיה וחקר החלל? איך אנחנו מגלים כוכבי לכת חדשים ומה אנחנו לומדים עליהם?",
            "תוכל לספר לי על הארכיטקטורה הקלאסית? איך השפיעו הרומאים והיוונים על הבנייה המודרנית?",
            "אני מעוניין בתחום הרובוטיקה. איך בונים רובוטים אוטונומיים ומה הטכנולוגיות שמאפשרות להם לנווט בסביבה?",
            "בואו נדבר על אנתרופולוגיה. איך התפתחה החברה האנושית ומה הגורמים העיקריים שהשפיעו על התרבויות השונות?",
            "תוכל להסביר לי על נוירוביולוגיה? איך עובד המערכת העצבית ואיך המוח מעבד אותות חושיים?",
            "מה אתה יודע על מתמטיקה טהורה? תוכל להסביר על תורת הקבוצות, טופולוגיה ואלגברה מופשטת?",
            "אני רוצה ללמוד על הנדסת תוכנה מתקדמת. איך מעצבים מערכות גדולות, מה זה clean code ואיך מבצעים testing נכון?",
            "תוכל לספר לי על הפילוסופיה המזרחית - בודהיזם, הינדואיזם, וטאואיזם? איך השפות הפילוסופיות האלה רואות את המציאות והקיום?",
            "אני מעוניין ללמוד על כלכלה התנהגותית. איך הטיות קוגניטיביות משפיעות על החלטות כלכליות ומה אפשר ללמוד מכך על שווקים?",
            "תוכל להסביר לי על תורת האבולוציה ועל הראיות התומכות בה? איך האבולוציה ממשיכה להשפיע על האנושות כיום?",
            "מה אתה יודע על פילוסופיה של המדע? איך אנחנו יודעים מה שאנחנו יודעים ומה זה אומר על טבע הידע המדעי?",
            "אני רוצה להבין את עולם האמנות הדיגיטלית. איך טכנולוגיות חדשות כמו VR, AR ו-AI משנות את היצירה והצריכה האמנותית?",
            "תוכל לספר לי על תחום הביואתיקה? איזה דילמות מוסריות עולות מהתקדמות הרפואית והמחקר הביולוגי?",
            "מה המשמעות של קיימות סביבתית בעידן המודרני? איך עסקים וחברות יכולים לאמץ פרקטיקות ירוקות באופן אפקטיבי?",
            "אני מעוניין בתחום הפסיכולוגיה החברתית. איך קבוצות משפיעות על התנהגות אינדיבידואלית ומה נוכל ללמוד על דינמיקות חברתיות?",
            "תוכל להסביר על עולם המוזיקה הקלאסית? מה ההבדלים בין התקופות השונות ואיך המוזיקה השתנתה לאורך ההיסטוריה?",
            "מה אתה יודע על תורת המשחקים? איך עקרונות מתמטיים יכולים לעזור להבין אסטרטגיות וקבלת החלטות במצבים תחרותיים?",
            "אני רוצה ללמוד על תחום הבלשנות. איך שפות מתפתחות ומשתנות, ומה אפשר ללמוד על החשיבה האנושית מחקר השפה?",
            "תוכל לספר לי על תולדות הרפואה? איך התפתחו הידע והטכניקות הרפואיות מימי קדם ועד היום?",
            "מה המשמעות של מהפכת המידע בעידן שלנו? איך הגישה הבלתי מוגבלת למידע משנה את החברה והפוליטיקה?",
            "אני מעוניין בתחום הארכיאולוגיה. איך חוקרים מגלים ומפענחים את העבר האנושי דרך ממצאים חומריים?",
            "תוכל להסביר על הקשר בין מתמטיקה לטבע? איך נוסחאות מתמטיות מתארות בדיוק כה רב תופעות פיזיקליות?",
            "מה אתה יודע על תחום הסוציולוגיה? איך חוקרים חברתיים בוחנים מבנים חברתיים, חילוק מעמדי ושינויים חברתיים?",
            "אני רוצה להבין את תחום האקולוגיה. איך מערכות אקולוגיות עובדות ומה הקשרים המורכבים בין יצורים חיים לסביבתם?",
            "תוכל לספר על ההיסטוריה של המדע המערבי? איך התפתח המדע מימי יוון העתיקה ועד המהפכה המדעית?",
            "מה המשמעות של גלובליזציה בעידן המודרני? איך תהליכי הגלובליזציה משפיעים על כלכלה, תרבות ופוליטיקה?",
            "אני מעוניין בתחום הפילוסופיה הפוליטית. איך אידיאולוגיות שונות מגדירות את תפקיד המדינה ואת זכויות הפרט?",
            "תוכל להסביר על תחום הגנטיקה המודרנית? איך טכנולוגיות כמו CRISPR משנות את היכולת שלנו לערוך ולהבין DNA?",
            "מה ההשפעה של מדיה דיגיטלית על התודעה הציבורית? איך פלטפורמות חברתיות משנות את האופן שבו אנחנו צורכים מידע ומתקשרים?"
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
    
    def count_response_tokens(self, response: str) -> int:
        """Count tokens in response text"""
        try:
            return len(self.tokenizer.encode(response))
        except Exception as e:
            logger.warning(f"Response token counting failed: {e}")
            # Fallback: rough estimation (4 chars per token average)
            return len(response) // 4
    
    
    
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
                    gpu_cache_usage=metrics.get('gpu_cache_usage_perc', 0.0)
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
        """Send a single chat request to the API and track metrics"""
        request_id = user.request_count
        user.request_count += 1
        
        # Prepare conversation with new user message
        user.conversation.append({"role": "user", "content": prompt})
        
        # Count tokens in the full conversation context
        context_tokens = self.count_conversation_tokens(user.conversation)
        total_context = self.calculate_total_context_length()
        
        # logger.info(f"User {user.user_id} starting request {request_id+1} "
        logger.info(f"(context: {context_tokens} tokens, total: {total_context} tokens)")

        # Create metrics object
        send_time = time.time()
        metrics = RequestMetrics(
            user_id=user.user_id,
            request_id=request_id,
            prompt=prompt,
            context_length=context_tokens,
            start_time=send_time,
            total_context_at_start=total_context
        )
        
        # Prepare request payload (like frontend)
        payload = {
            "messages": user.conversation,
            "session_id": user.session_id,
            "stream": True
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
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
                    
                    # Track streaming metrics
                    assistant_response = ""
                    first_token_received = False
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        
                        if line_str.startswith("data: "):
                            # Capture first token time
                            if not first_token_received:
                                metrics.first_token_time = time.time()
                                metrics.queue_time = metrics.first_token_time - send_time
                                metrics.ttft = metrics.queue_time
                                first_token_received = True
                            
                            data_str = line_str[6:]  # Remove "data: " prefix
                            
                            if data_str == "[DONE]":
                                metrics.end_time = time.time()
                                break
                            
                            try:
                                data = json.loads(data_str)
                                
                                content = None
                                if "error" in data:
                                    metrics.error = data["error"]
                                    metrics.end_time = time.time()
                                    user.empty_response_count += 1
                                    # Remove user message on error
                                    user.conversation.pop()
                                    return metrics
                                    
                                elif "choices" in data and len(data["choices"]) > 0:
                                    choice = data["choices"][0]
                                    if "delta" in choice and "content" in choice["delta"]:
                                        content = choice["delta"]["content"]
                                
                                if content:
                                    assistant_response += content
                                    
                            except json.JSONDecodeError:
                                continue
                    
                    # Process results
                    if assistant_response:
                        # Success: Add assistant response
                        user.conversation.append({"role": "assistant", "content": assistant_response})
                        
                        # Calculate metrics
                        if metrics.first_token_time and metrics.end_time:
                            metrics.response_tokens = self.count_response_tokens(assistant_response)
                            metrics.generation_time = metrics.end_time - metrics.first_token_time
                            
                            if metrics.generation_time > 0 and metrics.response_tokens > 0:
                                metrics.tokens_per_second = metrics.response_tokens / metrics.generation_time
                        
                        logger.info(f"User {user.user_id} request {request_id+1} completed: {len(assistant_response)} chars")
                    else:
                        # Remove user message on failure
                        user.conversation.pop()
                        logger.error(f"User {user.user_id} request {request_id+1} failed - no response received")
                        

                        
        except Exception as e:
            metrics.error = str(e)
            logger.error(f"Request failed for user {user.user_id}: {e} (failure #{user.empty_response_count})")
            
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
                
            # logger.info(f"User {user_id} sending request {i+1}: {prompt[:50]}...")
            
            # Send request and collect metrics
            metrics = await self.send_chat_request(user, prompt)
            self.request_metrics.append(metrics)
            
            # Log metrics
            if metrics.error:
                logger.error(f"User {user_id} request {i+1} failed: {metrics.error}")
            else:
                logger.info(f"User {user_id} request {i+1} completed: "
                           f"Context={metrics.context_length} tokens, "
                           f"Queue={metrics.queue_time:.3f}s, "
                           f"Generation={metrics.generation_time:.3f}s, "
                           f"Tokens Generated={metrics.response_tokens}, "
                           f"TPS={metrics.tokens_per_second:.1f}")
            
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

        # Create figure with 5 subplots (3x2 grid, one empty)
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
                    marker='o', linewidth=2, markersize=6)
        
        ax1.set_xlabel('Request Number')
        ax1.set_ylabel('Time to First Token (seconds)')
        ax1.set_title('Time to First Token per User')
        ax1.set_ylim(bottom=0)
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
                    marker='s', linewidth=2, markersize=6)
        
        ax2.set_xlabel('Request Number')
        ax2.set_ylabel('Token Generation Speed (tokens/sec)')
        ax2.set_title('Token Generation Speed per User')
        ax2.set_ylim(bottom=0)
        ax2.grid(True, alpha=0.3)
        
        # 3. Token Generation Speed per User vs Context Length
        ax3 = axes[1, 0]
        
        # Collect data for each user: context length vs token speed
        user_context_data = defaultdict(list)
        user_speed_data = defaultdict(list)
        
        for req in successful_requests:
            if req.tokens_per_second is not None and req.context_length is not None:
                user_context_data[req.user_id].append(req.context_length)
                user_speed_data[req.user_id].append(req.tokens_per_second)
        
        if user_context_data and user_speed_data:
            # Create line chart for each user
            colors = plt.cm.tab10(np.linspace(0, 1, len(user_context_data)))
            
            for i, user_id in enumerate(sorted(user_context_data.keys())):
                contexts = user_context_data[user_id]
                speeds = user_speed_data[user_id]
                
                if len(contexts) > 0 and len(speeds) > 0:
                    # Sort data by context length for proper line connection
                    sorted_data = sorted(zip(contexts, speeds))
                    sorted_contexts = [x[0] for x in sorted_data]
                    sorted_speeds = [x[1] for x in sorted_data]
                    
                    # Create line chart with markers
                    ax3.plot(sorted_contexts, sorted_speeds, 
                            marker='o', linewidth=2, markersize=6,
                            color=colors[i % len(colors)], alpha=0.8)
            
            ax3.set_xlabel('Context Length (tokens)')
            ax3.set_ylabel('Token Generation Speed (tokens/sec)')
            ax3.set_title('Token Generation Speed vs Context Length per User')
            ax3.set_ylim(bottom=0)
            ax3.grid(True, alpha=0.3)
        else:
            ax3.text(0.5, 0.5, 'No token speed vs context data available', 
                    ha='center', va='center', transform=ax3.transAxes,
                    fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            ax3.set_title('Token Generation Speed vs Context Length per User\n(Data unavailable)')
        
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
            ax4.set_ylim(bottom=0)
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'No token speed vs context data available', 
                    ha='center', va='center', transform=ax4.transAxes,
                    fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            ax4.set_title('Token Generation Speed vs Total Context Length\n(Data unavailable)')
        
        # 5. Request Status - Line Chart (running vs waiting requests)
        ax5 = axes[2, 0]
        if self.system_snapshots:
            timestamps = [s.timestamp for s in self.system_snapshots]
            running_requests = [s.running_requests for s in self.system_snapshots]
            waiting_requests = [s.waiting_requests for s in self.system_snapshots]
            
            ax5.plot(timestamps, running_requests, 
                    marker='o', label='Running Requests', linewidth=2, markersize=4, color='green')
            ax5.plot(timestamps, waiting_requests, 
                    marker='s', label='Waiting Requests', linewidth=2, markersize=4, color='red')
            
            ax5.set_xlabel('Time (seconds)')
            ax5.set_ylabel('Number of Requests')
            ax5.set_title('Request Status Over Time')
            ax5.set_ylim(bottom=0)
            ax5.legend()
            ax5.grid(True, alpha=0.3)
        else:
            ax5.text(0.5, 0.5, 'No system snapshots available', 
                    ha='center', va='center', transform=ax5.transAxes,
                    fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            ax5.set_title('Request Status Over Time\n(Data unavailable)')
        
        # Hide the empty subplot
        axes[2, 1].set_visible(False)
        
        plt.tight_layout()
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_path = f"{self.instance_model}_simulation_results_{timestamp}.png"
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
            # Queue time (TTFT) analysis
            queue_values = [req.queue_time for req in successful_requests if req.queue_time is not None]
            if queue_values:
                print(f"\nQueue Time (TTFT) Analysis:")
                print(f"  - Mean Queue Time: {np.mean(queue_values):.3f}s")
                print(f"  - Median Queue Time: {np.median(queue_values):.3f}s")
                print(f"  - Min Queue Time: {np.min(queue_values):.3f}s")
                print(f"  - Max Queue Time: {np.max(queue_values):.3f}s")
                print(f"  - Data points: {len(queue_values)}/{len(successful_requests)}")
            
            # Generation time analysis
            gen_values = [req.generation_time for req in successful_requests if req.generation_time is not None]
            if gen_values:
                print(f"\nGeneration Time Analysis:")
                print(f"  - Mean Generation Time: {np.mean(gen_values):.3f}s")
                print(f"  - Median Generation Time: {np.median(gen_values):.3f}s")
                print(f"  - Min Generation Time: {np.min(gen_values):.3f}s")
                print(f"  - Max Generation Time: {np.max(gen_values):.3f}s")
                print(f"  - Data points: {len(gen_values)}/{len(successful_requests)}")
            
            # Token generation speed analysis
            tps_values = [req.tokens_per_second for req in successful_requests if req.tokens_per_second is not None]
            if tps_values:
                print(f"\nToken Generation Speed Analysis:")
                print(f"  - Mean TPS: {np.mean(tps_values):.1f} tokens/s")
                print(f"  - Median TPS: {np.median(tps_values):.1f} tokens/s")
                print(f"  - Min TPS: {np.min(tps_values):.1f} tokens/s")
                print(f"  - Max TPS: {np.max(tps_values):.1f} tokens/s")
                print(f"  - Data points: {len(tps_values)}/{len(successful_requests)}")
            
            # Response tokens analysis
            token_values = [req.response_tokens for req in successful_requests if req.response_tokens > 0]
            if token_values:
                print(f"\nResponse Token Analysis:")
                print(f"  - Mean Response Tokens: {np.mean(token_values):.0f}")
                print(f"  - Median Response Tokens: {np.median(token_values):.0f}")
                print(f"  - Min Response Tokens: {np.min(token_values)}")
                print(f"  - Max Response Tokens: {np.max(token_values)}")
                print(f"  - Data points: {len(token_values)}/{len(successful_requests)}")
            
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
        request_csv_path = f"{self.instance_model}_simulation_requests_{timestamp}.csv"
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
                    'gpu_cache_usage': snapshot.gpu_cache_usage
                })
            
            system_df = pd.DataFrame(system_data)
            system_csv_path = f"{self.instance_model}_simulation_system_{timestamp}.csv"
            system_df.to_csv(system_csv_path, index=False)
            logger.info(f"System metrics saved to {system_csv_path}")

async def main():
    """Main function to run the simulation"""
    # Configuration
    api_url = "http://localhost:8090"  # Change to your API URL
    model_name = "gaunernst/gemma-3-12b-it-qat-autoawq"  # Your model name
    num_users = 25  # Number of concurrent users
    
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
