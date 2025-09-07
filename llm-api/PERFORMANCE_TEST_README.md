# LLM Performance Testing

This directory contains a comprehensive performance testing suite for your LLM API that simulates real-world usage patterns with multiple concurrent users.

## Overview

The performance test simulates **10 concurrent users** chatting with the model simultaneously, each with increasing context lengths to test how the system handles growing conversation histories. This mimics real chatbot usage where conversations get longer over time.

## What It Tests

### Key Metrics
- **Time to First Token (TTFT)**: How long until the first response token is generated
- **Token Generation Speed**: Tokens per second during response generation  
- **Total Response Time**: Complete time from request to response completion
- **Context Length Impact**: How performance changes as conversations grow longer
- **Queue Time**: Time spent waiting when the system is under load

### Test Scenario
- **10 users** start inference with **5-second delays** between each user
- Each user sends requests with **10-second intervals** between their own requests
- **Progressive complexity**: Each request has more context than the previous
- **Automatic stopping**: Test stops when only one request is being processed and others are queued

## Quick Start

### Prerequisites
1. Make sure your LLM API is running:
   ```bash
   cd llm-api
   python -m uvicorn main:app --host 0.0.0.0 --port 8090
   ```

2. In another terminal, run the performance test:
   ```bash
   cd llm-api
   ./run_performance_test.sh
   ```

### Manual Setup
If you prefer to set up manually:

```bash
# Install dependencies
pip install -r performance_test_requirements.txt

# Run the test
python3 performance_test.py
```

## Configuration

You can modify the test parameters by editing `performance_test.py`:

```python
# Test configuration
self.num_users = 10              # Number of concurrent users
self.user_start_delay = 5.0      # Seconds between user starts  
self.request_delay = 10.0        # Seconds between requests per user
```

You can also change the API endpoint:
```python
api_url = "http://localhost:8090"  # Change to your API URL
```

## Output

The test generates several outputs:

### 1. Real-time Logs
- User activity and request status
- Performance metrics for each request
- Error reporting

### 2. Performance Graphs (`performance_test_YYYYMMDD_HHMMSS.png`)
- Time to First Token vs Context Length
- Token Generation Speed vs Context Length  
- Total Response Time vs Context Length
- Performance trends by user over time

### 3. Detailed Metrics CSV (`performance_metrics_YYYYMMDD_HHMMSS.csv`)
- Complete data for all successful requests
- Can be imported into Excel or other analysis tools

### 4. Summary Report
Printed to console with:
- Overall statistics (success/failure rates)
- TTFT percentiles and averages
- Token generation speed statistics
- Performance breakdown by context length ranges

## Understanding the Results

### Good Performance Indicators
- **TTFT < 2 seconds**: Fast initial response
- **Token Speed > 20 tokens/sec**: Good generation throughput
- **Consistent performance**: Metrics don't degrade significantly with context length
- **Low failure rate**: < 5% failed requests

### Performance Issues to Watch For
- **High TTFT variance**: Indicates queueing or resource contention
- **Degrading speed with context**: May indicate memory or attention bottlenecks
- **Request failures**: Could indicate timeout or resource exhaustion

### Context Length Impact
The test uses progressively longer prompts to simulate real conversations:
1. Short greeting (< 50 tokens)
2. Medium question (< 200 tokens) 
3. Complex topic (< 500 tokens)
4. Technical discussion (< 1000 tokens)
5. Detailed research query (< 1500 tokens)

## Troubleshooting

### Common Issues

**"API is not healthy"**
- Ensure your LLM API is running on the correct port
- Check that vLLM backend is properly started
- Verify the health endpoint returns status "healthy"

**"Connection refused"**
- Check if the API URL is correct
- Ensure no firewall is blocking the connection
- Verify the API is listening on the expected interface

**"Tokenizer loading failed"**
- The script will fall back to a generic tokenizer
- For accurate token counts, ensure the model tokenizer is available

**High failure rates**
- May indicate the system is overloaded
- Try reducing `num_users` or increasing `request_delay`
- Check system resources (CPU, GPU, memory)

## Customization

### Adding Custom Prompts
Edit the `self.prompts` list in `PerformanceTester.__init__()`:

```python
self.prompts = [
    "Your custom prompt 1",
    "Your custom prompt 2 with more context...",
    # Add more prompts with increasing complexity
]
```

### Different Test Patterns
You can modify `simulate_user()` to implement different testing patterns:
- Burst testing (many requests quickly)
- Sustained load (continuous requests)
- Mixed workloads (different prompt types)

### Additional Metrics
The `RequestMetrics` class can be extended to capture more data:
- Memory usage
- GPU utilization  
- Network latency
- Custom business metrics

## Integration with CI/CD

The performance test can be integrated into your deployment pipeline:

```bash
# Run test and check if performance meets thresholds
python3 performance_test.py
if [ $? -eq 0 ]; then
    echo "Performance test passed"
else
    echo "Performance test failed"
    exit 1
fi
```

You can modify the script to exit with error codes based on performance thresholds.

---

For questions or issues with the performance testing suite, check the logs and ensure your LLM API is properly configured and running.
