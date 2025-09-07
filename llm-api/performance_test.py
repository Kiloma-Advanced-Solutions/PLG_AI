#!/usr/bin/env python3
"""
Performance Testing Script for LLM API
Tests concurrent inference with multiple users and increasing context lengths
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from transformers import AutoTokenizer
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    user_id: int
    request_id: int
    prompt: str
    context_length: int  # tokens in prompt
    start_time: float
    first_token_time: Optional[float] = None
    end_time: Optional[float] = None
    response_tokens: int = 0
    total_tokens: int = 0
    error: Optional[str] = None
    queue_time: Optional[float] = None  # Time spent waiting in queue
    
    @property
    def time_to_first_token(self) -> Optional[float]:
        """Time from request start to first token"""
        if self.first_token_time:
            return self.first_token_time - self.start_time
        return None
    
    @property
    def total_time(self) -> Optional[float]:
        """Total time from request start to completion"""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def tokens_per_second(self) -> Optional[float]:
        """Token generation speed (tokens/second)"""
        if self.end_time and self.first_token_time and self.response_tokens > 0:
            generation_time = self.end_time - self.first_token_time
            if generation_time > 0:
                return self.response_tokens / generation_time
        return None

@dataclass
class UserState:
    """State for a single simulated user"""
    user_id: int
    session_id: str
    conversation: List[Dict[str, str]] = field(default_factory=list)
    request_count: int = 0
    active: bool = True
    
class PerformanceTester:
    """Main performance testing class"""
    
    def __init__(self, api_url: str = "http://localhost:8090", model_name: str = "gaunernst/gemma-3-12b-it-qat-autoawq"):
        self.api_url = api_url
        self.model_name = model_name
        self.chat_endpoint = f"{api_url}/api/chat/stream"
        self.health_endpoint = f"{api_url}/api/health"
        
        # Test configuration
        self.num_users = 10
        self.user_start_delay = 5.0  # seconds between user starts
        self.request_delay = 10.0    # seconds between requests per user
        
        # Initialize tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            logger.info(f"Loaded tokenizer for {model_name}")
        except Exception as e:
            logger.warning(f"Could not load tokenizer for {model_name}: {e}")
            # Fallback to a generic tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b")
            logger.info("Using fallback tokenizer: google/gemma-2b")
        
        # Metrics storage
        self.metrics: List[RequestMetrics] = []
        self.users: List[UserState] = []
        
        # Test prompts that increase in complexity
        self.prompts = [
            "שלום, איך אתה?",
            "תוכל לספר לי על ההיסטוריה של ישראל?",
            "אני רוצה לדעת על הטכנולוגיה החדשה בתחום הבינה המלאכותית. תוכל להסביר לי על מודלי שפה גדולים ואיך הם עובדים?",
            "בואו נדבר על פיתוח תוכנה. אני מעוניין לדעת על ארכיטקטורות מיקרו-שירותים, איך לעצב מערכות מבוזרות, ומה הן השיטות הטובות ביותר לניהול מסדי נתונים בסביבות ענן.",
            "אני חוקר את התחום של למידת מכונה ובינה מלאכותית. תוכל להסביר לי על האלגוריתמים השונים כמו רשתות נוירונים, עצי החלטה, SVM, ואיך הם משתלבים במערכות ייצור? גם אשמח לדעת על אתגרים בעיבוד נתונים גדולים.",
        ]
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using the model's tokenizer"""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            # Rough estimation: ~4 characters per token for Hebrew
            return len(text) // 4
    
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
    
    async def send_chat_request(self, user: UserState, prompt: str) -> RequestMetrics:
        """Send a single chat request and measure performance"""
        request_id = user.request_count
        user.request_count += 1
        
        # Add user message to conversation
        user.conversation.append({"role": "user", "content": prompt})
        
        # Count tokens in the full conversation context
        full_context = json.dumps(user.conversation, ensure_ascii=False)
        context_tokens = self.count_tokens(full_context)
        
        # Create metrics object
        metrics = RequestMetrics(
            user_id=user.user_id,
            request_id=request_id,
            prompt=prompt,
            context_length=context_tokens,
            start_time=time.time()
        )
        
        # Prepare request payload
        payload = {
            "messages": user.conversation.copy(),
            "session_id": user.session_id,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 512
        }
        
        try:
            async with aiohttp.ClientSession() as session:
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
                    first_content_received = False
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        
                        if line_str.startswith("data: "):
                            data_str = line_str[6:]  # Remove "data: " prefix
                            
                            if data_str == "[DONE]":
                                metrics.end_time = time.time()
                                break
                            
                            try:
                                data = json.loads(data_str)
                                if "content" in data and not first_content_received:
                                    metrics.first_token_time = time.time()
                                    first_content_received = True
                                
                                if "content" in data:
                                    assistant_response += data["content"]
                                    
                            except json.JSONDecodeError:
                                continue
                    
                    # Add assistant response to conversation
                    if assistant_response:
                        user.conversation.append({"role": "assistant", "content": assistant_response})
                        metrics.response_tokens = self.count_tokens(assistant_response)
                        metrics.total_tokens = context_tokens + metrics.response_tokens
                    
                    if not metrics.end_time:
                        metrics.end_time = time.time()
                        
        except Exception as e:
            metrics.error = str(e)
            metrics.end_time = time.time()
            logger.error(f"Request failed for user {user.user_id}: {e}")
        
        return metrics
    
    async def simulate_user(self, user_id: int, start_delay: float):
        """Simulate a single user's behavior"""
        # Wait for start delay
        await asyncio.sleep(start_delay)
        
        user = UserState(
            user_id=user_id,
            session_id=f"perf_test_user_{user_id}_{int(time.time())}"
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
            self.metrics.append(metrics)
            
            # Log metrics
            if metrics.error:
                logger.error(f"User {user_id} request {i+1} failed: {metrics.error}")
            else:
                ttft = metrics.time_to_first_token
                tps = metrics.tokens_per_second
                logger.info(f"User {user_id} request {i+1} completed: "
                          f"TTFT={ttft:.2f}s, TPS={tps:.1f}, Context={metrics.context_length} tokens")
            
            # Wait before next request (except for last request)
            if i < len(self.prompts) - 1:
                await asyncio.sleep(self.request_delay)
        
        user.active = False
        logger.info(f"User {user_id} completed simulation")
    
    def should_stop_simulation(self) -> bool:
        """Check if simulation should stop based on queue conditions"""
        # Stop when only one request is being processed and others are in queue
        # This is a simplified heuristic - in real scenarios you'd check actual queue metrics
        active_users = sum(1 for user in self.users if user.active)
        
        # Stop if all users have started and most have completed their requests
        if len(self.users) >= self.num_users:
            completed_users = sum(1 for user in self.users if not user.active)
            if completed_users >= self.num_users - 1:  # Only 1 user still active
                return True
        
        return False
    
    async def run_test(self):
        """Run the complete performance test"""
        logger.info("Starting performance test...")
        
        # Check API health
        if not await self.check_api_health():
            logger.error("API is not healthy. Aborting test.")
            return
        
        # Start all users with delays
        tasks = []
        for user_id in range(self.num_users):
            start_delay = user_id * self.user_start_delay
            task = asyncio.create_task(self.simulate_user(user_id, start_delay))
            tasks.append(task)
        
        # Monitor for stop condition
        while not self.should_stop_simulation():
            await asyncio.sleep(1)
        
        # Cancel remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete or be cancelled
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Performance test completed")
    
    def generate_report(self):
        """Generate detailed performance report with graphs"""
        if not self.metrics:
            logger.error("No metrics collected")
            return
        
        # Create DataFrame for analysis
        data = []
        for m in self.metrics:
            if not m.error:  # Only include successful requests
                data.append({
                    'user_id': m.user_id,
                    'request_id': m.request_id,
                    'context_length': m.context_length,
                    'time_to_first_token': m.time_to_first_token,
                    'total_time': m.total_time,
                    'tokens_per_second': m.tokens_per_second,
                    'response_tokens': m.response_tokens,
                    'total_tokens': m.total_tokens
                })
        
        if not data:
            logger.error("No successful requests to analyze")
            return
        
        df = pd.DataFrame(data)
        
        # Create visualizations
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('LLM Performance Test Results', fontsize=16)
        
        # 1. Time to First Token vs Context Length
        axes[0, 0].scatter(df['context_length'], df['time_to_first_token'], alpha=0.7)
        axes[0, 0].set_xlabel('Context Length (tokens)')
        axes[0, 0].set_ylabel('Time to First Token (seconds)')
        axes[0, 0].set_title('Time to First Token vs Context Length')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Token Generation Speed vs Context Length
        axes[0, 1].scatter(df['context_length'], df['tokens_per_second'], alpha=0.7, color='orange')
        axes[0, 1].set_xlabel('Context Length (tokens)')
        axes[0, 1].set_ylabel('Tokens per Second')
        axes[0, 1].set_title('Token Generation Speed vs Context Length')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Total Response Time vs Context Length
        axes[1, 0].scatter(df['context_length'], df['total_time'], alpha=0.7, color='green')
        axes[1, 0].set_xlabel('Context Length (tokens)')
        axes[1, 0].set_ylabel('Total Response Time (seconds)')
        axes[1, 0].set_title('Total Response Time vs Context Length')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Performance Over Time (by user)
        for user_id in df['user_id'].unique():
            user_data = df[df['user_id'] == user_id]
            axes[1, 1].plot(user_data['request_id'], user_data['tokens_per_second'], 
                          marker='o', label=f'User {user_id}', alpha=0.7)
        axes[1, 1].set_xlabel('Request Number')
        axes[1, 1].set_ylabel('Tokens per Second')
        axes[1, 1].set_title('Token Generation Speed by User Over Time')
        axes[1, 1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_path = f"performance_test_{timestamp}.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        logger.info(f"Performance graphs saved to {plot_path}")
        
        # Print detailed summary
        print("\n" + "="*80)
        print("PERFORMANCE TEST SUMMARY")
        print("="*80)
        
        print(f"\nTest Configuration:")
        print(f"  - Number of users: {self.num_users}")
        print(f"  - User start delay: {self.user_start_delay}s")
        print(f"  - Request delay: {self.request_delay}s")
        print(f"  - Model: {self.model_name}")
        
        print(f"\nOverall Statistics:")
        print(f"  - Total requests: {len(self.metrics)}")
        print(f"  - Successful requests: {len(df)}")
        print(f"  - Failed requests: {len(self.metrics) - len(df)}")
        
        if len(df) > 0:
            print(f"\nTime to First Token (TTFT):")
            print(f"  - Mean: {df['time_to_first_token'].mean():.2f}s")
            print(f"  - Median: {df['time_to_first_token'].median():.2f}s")
            print(f"  - 95th percentile: {df['time_to_first_token'].quantile(0.95):.2f}s")
            print(f"  - Max: {df['time_to_first_token'].max():.2f}s")
            
            print(f"\nToken Generation Speed:")
            print(f"  - Mean: {df['tokens_per_second'].mean():.1f} tokens/s")
            print(f"  - Median: {df['tokens_per_second'].median():.1f} tokens/s")
            print(f"  - Min: {df['tokens_per_second'].min():.1f} tokens/s")
            print(f"  - Max: {df['tokens_per_second'].max():.1f} tokens/s")
            
            print(f"\nTotal Response Time:")
            print(f"  - Mean: {df['total_time'].mean():.2f}s")
            print(f"  - Median: {df['total_time'].median():.2f}s")
            print(f"  - 95th percentile: {df['total_time'].quantile(0.95):.2f}s")
            print(f"  - Max: {df['total_time'].max():.2f}s")
            
            print(f"\nContext Length Analysis:")
            print(f"  - Mean context length: {df['context_length'].mean():.0f} tokens")
            print(f"  - Max context length: {df['context_length'].max():.0f} tokens")
            
            # Performance by context length ranges
            print(f"\nPerformance by Context Length:")
            for min_len, max_len in [(0, 100), (100, 500), (500, 1000), (1000, float('inf'))]:
                mask = (df['context_length'] >= min_len) & (df['context_length'] < max_len)
                subset = df[mask]
                if len(subset) > 0:
                    range_name = f"{min_len}-{max_len if max_len != float('inf') else '∞'} tokens"
                    print(f"  {range_name}: {len(subset)} requests, "
                          f"avg TTFT: {subset['time_to_first_token'].mean():.2f}s, "
                          f"avg TPS: {subset['tokens_per_second'].mean():.1f}")
        
        # Save detailed metrics to CSV
        csv_path = f"performance_metrics_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Detailed metrics saved to {csv_path}")
        
        print(f"\nFiles generated:")
        print(f"  - Performance graphs: {plot_path}")
        print(f"  - Detailed metrics: {csv_path}")
        print("="*80)

async def main():
    """Main function to run the performance test"""
    # You can modify these parameters as needed
    api_url = "http://localhost:8090"  # Change to your API URL
    model_name = "gaunernst/gemma-3-12b-it-qat-autoawq"  # Your model name
    
    tester = PerformanceTester(api_url, model_name)
    
    try:
        await tester.run_test()
        tester.generate_report()
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
