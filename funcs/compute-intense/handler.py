import time
import json
import random
import hashlib
import math

print(f"Global Sleep Starting...")
time.sleep(5)
print(f"Global Sleep Completed")

def cpu_intensive_work(duration_seconds):
    """
    Perform actual CPU-intensive calculations for the specified duration.
    This will generate real CPU load, not just sleep.
    """
    end_time = time.time() + duration_seconds
    iterations = 0
    result = 0
    
    print(f"Starting CPU-intensive work for {duration_seconds} seconds...")
    
    while time.time() < end_time:
        # Mathematical calculations (CPU intensive)
        for i in range(1000):
            result += math.sqrt(i) * math.sin(i) * math.cos(i)
            result += math.log(i + 1) * math.exp(i / 1000)
        
        # String hashing (CPU intensive)
        data = str(result).encode()
        for _ in range(100):
            data = hashlib.sha256(data).digest()
        
        # List operations (CPU and memory)
        temp_list = [i**2 for i in range(100)]
        temp_sum = sum(temp_list)
        result += temp_sum
        
        iterations += 1
    
    print(f"Completed {iterations} iterations of CPU work in {duration_seconds} seconds")
    return result

def handle(event, context):
    try:
        print(f"Compute-Time: {event.headers.get('Compute-Time')}")
    except:
        pass
    try:
        print(f"X-Start-Time: {event.headers.get('X-Start-Time')}")
    except:
        pass
    try:
        print(f"X-Call-Id: {event.headers.get('X-Call-Id')}")
    except:
        pass
    try:
        print(f"body: {json.loads(event.body)}")
    except:
        pass
    
    # Get compute time from header or default
    try:
        compute_time = int(event.headers.get('Compute-Time', 5))
        assignment_method = "Duration specified via 'Compute-Time' header."
    except:
        compute_time = random.randint(3, 10)
        assignment_method = "Randomly assigned duration."
    
    print(f"Will perform CPU-intensive work for {compute_time} seconds. {assignment_method}")
    
    # DO ACTUAL CPU WORK instead of sleeping!
    result = cpu_intensive_work(compute_time)
    
    print(f"Done with CPU work. Processed result: {result:.2e}")
    
    try:
        body_string = f"Hello from OpenFaaS compute-intense {event.headers.get('X-Tier')}! CPU work completed: {result:.2e}"
    except:
        body_string = f"Hello from OpenFaaS compute-intense! CPU work completed: {result:.2e}"
    
    return {
        "statusCode": 200,
        "body": body_string
    }
