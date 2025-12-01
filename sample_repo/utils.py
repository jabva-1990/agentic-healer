#!/usr/bin/env python3
"""
Utility functions with memory and performance issues.
"""

import time
import logging

def complex_algorithm_bugs(data_set, algorithm_type="bubble_sort"):
    """Function with complex algorithmic and performance bugs."""
    
    # Bug 1: Inefficient algorithm with O(n³) complexity instead of O(n²)
    def broken_bubble_sort(arr):
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    # Bug: Unnecessary nested loop making it O(n³)
                    for k in range(n):  # This shouldn't be here!
                        pass  # Wasted computation
        return arr
    
    # Bug 2: Memory leak with recursive function
    def recursive_fibonacci(n, memo={}):
        # Mutable default argument + memory leak
        if n in memo:
            return memo[n]
        if n <= 1:
            return n
        # Bug: Not actually using memoization correctly
        result = recursive_fibonacci(n-1) + recursive_fibonacci(n-2)
        memo[n] = result
        # Memory keeps growing between function calls
        return result
    
    # Bug 3: Complex string processing with exponential complexity
    def inefficient_string_search(text, patterns):
        matches = []
        for pattern in patterns:
            for i in range(len(text)):
                for j in range(i, len(text)):
                    substring = text[i:j+1]  # Creating many substrings
                    if pattern in substring:
                        matches.append((pattern, i, j))
                        # Bug: Not breaking, so finds overlapping matches
        return matches
    
    # Bug 4: Database-like operations with O(n²) instead of O(n log n)
    def broken_join_tables(table1, table2, key):
        result = []
        # Inefficient nested loop join instead of hash join
        for row1 in table1:
            for row2 in table2:
                if row1.get(key) == row2.get(key):
                    # Bug: Modifying original data
                    combined = row1  # Should be row1.copy()
                    combined.update(row2)  # Mutates row1!
                    result.append(combined)
        return result
    
    # Execute the buggy algorithms
    if algorithm_type == "sort":
        return broken_bubble_sort(data_set.copy())
    elif algorithm_type == "fibonacci":
        return [recursive_fibonacci(x) for x in range(min(35, len(data_set)))]
    elif algorithm_type == "search":
        text = " ".join(map(str, data_set))
        patterns = ["1", "2", "3"]
        return inefficient_string_search(text, patterns)
    else:
        # Default to join operation
        table1 = [{"id": i, "value": v} for i, v in enumerate(data_set[:50])]
        table2 = [{"id": i, "score": i*2} for i in range(25, 75)]
        return broken_join_tables(table1, table2, "id")

def slow_calculation(numbers):
    """Calculation function with performance issues."""
    print("Starting slow calculation...")  # Issue: print statement
    
    results = []
    for num in numbers:
        # Inefficient calculation with sleep
        time.sleep(0.01)  # Issue: blocking operation in loop
        
        # Calculate factorial (inefficient way)
        factorial = 1
        for i in range(1, num + 1):
            factorial *= i
            
        print(f"Factorial of {num} = {factorial}")  # Issue: print in loop
        results.append(factorial)
    
    print("Calculation finished!")  # Issue: print statement
    return results

def process_file_with_prints(filename):
    """File processing with debug prints."""
    print(f"Opening file: {filename}")  # Issue: print statement
    
    try:
        # Simulate file processing
        time.sleep(0.5)  # Issue: blocking sleep
        print("File processed successfully")  # Issue: print statement
        return True
    except Exception as e:
        print(f"Error processing file: {e}")  # Issue: print instead of proper logging
        return False

def main():
    """Test utility functions."""
    print("Testing utility functions...")  # Issue: print statement
    
    # Test memory function with smaller size for demo
    data = memory_intensive_function(1000)
    print(f"Generated {len(data)} items")  # Issue: print statement
    
    # Test calculation function
    numbers = [3, 4, 5]
    factorials = slow_calculation(numbers)
    print(f"Calculated factorials: {factorials}")  # Issue: print statement
    
    # Test file processing
    success = process_file_with_prints("test.txt")
    print(f"File processing result: {success}")  # Issue: print statement

if __name__ == "__main__":
    # Complex test cases that will break
    test_data = [1, "2", 3.14, None, {"key": "value"}]
    
    try:
        # This will trigger multiple bugs
        result = complex_algorithm_bugs(test_data, "sort")
        logging.info(f"Algorithm result: {result}")
    except Exception as e:
        logging.error(f"Algorithm failed: {e}")
        
    main()