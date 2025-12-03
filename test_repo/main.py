#!/usr/bin/env python3
"""
Sample Python file with intentional issues for testing the healing system
"""

import os
import json

def calculate_average(numbers):
    # Issue 1: Division by zero not handled
    return sum(numbers) / len(numbers)

def read_config():
    # Issue 2: File might not exist
    with open('config.json', 'r') as f:
        return json.load(f)

def process_data(data):
    # Issue 3: Missing type validation
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

def main():
    # Issue 4: Variables used before definition
    print(f"Processing {count} items")
    count = 10
    
    numbers = [1, 2, 3, 4, 5]
    avg = calculate_average(numbers)
    print(f"Average: {avg}")
    
    # Issue 5: Potential exception not caught
    config = read_config()
    processed = process_data(numbers)
    print(f"Processed: {processed}")

if __name__ == "__main__":
    main()