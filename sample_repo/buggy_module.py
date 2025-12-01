#!/usr/bin/env python3
"""
New module with import and logic errors for testing.
"""

# Complex import and logic errors
import os
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

# Complex logic errors and edge cases
def advanced_calculator(x, y, operation="add"):
    """Calculator with complex bugs and edge cases."""
    
    # Bug 1: Type confusion - not handling string numbers
    if isinstance(x, str) or isinstance(y, str):
        # Wrong: should convert to float, but using int() loses precision
        x = int(x)  # This will fail for "3.14" 
        y = int(y)
    
    # Bug 2: Complex conditional logic error
    if operation == "divide":
        # Wrong: checking y == 0 but not handling float precision issues
        if y == 0:
            raise ValueError("Cannot divide by zero")
        result = x / y
    elif operation == "sqrt":
        # Bug 3: Using wrong variable and missing import
        import math
        if x < 0:  # Should check x, but using y in calculation
            raise ValueError("Cannot take square root of negative number")
        result = math.sqrt(y)  # Wrong variable!
    elif operation == "power":
        # Bug 4: Memory and performance issue with large numbers
        if y > 1000:  # This will cause memory issues
            result = x ** y  # Exponential memory growth!
        else:
            result = pow(x, y)
    else:
        # Bug 5: Default case doesn't handle all operations
        result = x + y  # Always defaults to addition
    
    return result

def complex_threading_bug():
    """Function with complex threading and resource issues."""
    results = []
    lock = threading.Lock()
    
    def worker_function(item):
        # Bug 1: Race condition - accessing shared resource without proper locking
        results.append(item * 2)  # Should be protected by lock
        
        # Bug 2: Resource leak - opening files without closing
        file = open(f"temp_{item}.txt", "w")  
        file.write(str(item))
        # Missing: file.close() or context manager
        
        # Bug 3: Potential deadlock scenario
        lock.acquire()
        if item > 5:
            lock.acquire()  # Double acquisition - deadlock!
        lock.release()
    
    # Bug 4: Not waiting for threads to complete
    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(100):
            executor.submit(worker_function, i)
        # Missing: executor.shutdown(wait=True) or proper future handling
    
    return results  # Results may be incomplete due to race conditions

def complex_data_processing_bugs(data_source):
    """Complex data processing with multiple subtle bugs."""
    
    # Bug 1: Mutable default argument
    def process_items(items, processed_cache={}):
        # This cache persists between calls - major bug!
        for item in items:
            if item not in processed_cache:
                processed_cache[item] = item ** 2
        return processed_cache
    
    # Bug 2: Dictionary iteration modification
    user_data = {"user1": 100, "user2": 200, "user3": 0}
    for user_id, balance in user_data.items():
        if balance == 0:
            del user_data[user_id]  # RuntimeError: dictionary changed size during iteration
    
    # Bug 3: List index out of bounds with complex logic
    scores = [85, 92, 78, 96, 88]
    for i in range(len(scores)):
        if scores[i] > 90:
            # Wrong: comparing with next index without bounds check
            if scores[i + 1] > scores[i]:  # IndexError on last element
                scores[i] = scores[i] + 5
    
    # Bug 4: JSON handling without proper error handling
    config_data = '{"timeout": 30, "retries": invalid_json}'
    config = json.loads(config_data)  # JSONDecodeError
    
    # Bug 5: Complex string manipulation bug
    filename = "report_2024-12-01_final.pdf"
    # Wrong: assumes specific format but doesn't validate
    date_part = filename.split("_")[1].split("_")[0]  # May fail on different formats
    date_obj = datetime.strptime(date_part, "%Y-%m-%d")  # May fail on format mismatch
    
    return {"processed": True, "date": date_obj, "config": config}

# Syntax error at the end
if __name__ == "__main__":
    print("Testing buggy module")  # Fixed closing parenthesis