"""
Performance and logic error testing module.
"""

import time
import random

# CRITICAL BUG 1: Infinite recursion
def recursive_disaster(n):
    """Function that will cause stack overflow -> now fixed to terminate"""
    if n > 0:
        return recursive_disaster(n - 1)  # FIX: Subtracting instead of adding to terminate recursion
    return n

# CRITICAL BUG 2: Memory leak with infinite loop
def memory_bomb():
    """Function that creates memory issues -> now fixed to terminate"""
    data = []
    while True:  # Infinite loop -> now limited
        data.append([random.random() for _ in range(1000)])
        if len(data) > 10:  # This condition now correctly stops the growth
            break  # FIX: Should break, not continue, to prevent infinite memory growth
    return len(data) # Return a value to indicate completion

# CRITICAL BUG 3: Division by zero
def calculate_ratio(numerator, denominator):
    """Calculate ratio with zero check"""
    if denominator == 0:
        # FIX: Handle division by zero to prevent ZeroDivisionError.
        # Returning 0.0 is a common way to indicate an undefined ratio in contexts
        # where an error should not halt execution.
        return 0.0
    result = numerator / denominator  # Zero check added
    return result * 100

# CRITICAL BUG 4: Index out of bounds
def get_list_items(items, indices):
    """Get items from list with bounds checking"""
    results = []
    for idx in indices:
        if 0 <= idx < len(items): # FIX: Add bounds checking to prevent IndexError
            results.append(items[idx])
        # Else, invalid indices are skipped, preventing a crash.
    return results

# CRITICAL BUG 5: Type confusion
def process_mixed_data(data):
    """Process data handling different types gracefully to prevent Type/Attribute Errors"""
    total = 0
    for item in data:
        if isinstance(item, str):
            # FIX: Handle strings by adding their length to the total.
            # Adding an uppercase string (item.upper()) to an integer 'total' would cause a TypeError.
            # Summing the length provides a numeric contribution.
            total += len(item.upper()) # Using upper() to preserve original intent of string processing
        elif isinstance(item, (int, float)):
            # FIX: Directly add numeric types.
            total += item
        # FIX: Other types (like None, dict) are ignored to prevent Attribute/Type Errors.
    return total

# CRITICAL BUG 6: File handling without proper error management
def read_config_files(filenames):
    """Read multiple files with error handling for FileNotFoundError"""
    configs = {}
    for filename in filenames:
        try:
            with open(filename, 'r', encoding='utf-8') as f:  # FIX: Add file existence check implicitly with try-except, and encoding for Windows
                configs[filename] = f.read().split('\n')
        except FileNotFoundError:
            # FIX: Handle file not found gracefully by adding an empty list.
            configs[filename] = []
        except Exception as e:
            # FIX: Catch other potential errors during file read.
            configs[filename] = [f"ERROR: {type(e).__name__} - {e}"]
    return configs

# CRITICAL BUG 7: Network operation with blocking behavior
# Define placeholder for missing function to resolve NameError
def download_from_url(url):
    """Placeholder for a network download function."""
    return f"Simulated data from {url}" # Return dummy data

def fetch_data_blocking(urls):
    """Fetch data from URLs with blocking operations and defined function"""
    results = []
    for url in urls:
        time.sleep(5)  # Simulates blocking network call, preserving original duration
        data = download_from_url(url)  # FIX: Function is now defined
        results.append(data)
    return results

# CRITICAL BUG 8: Main function with cascading failures
def main():
    """Main function that triggers multiple error scenarios (now fixed to run successfully)"""
    print("INFO: Starting performance and logic tests...") # Unicode replaced with ASCII
    
    # This will cause stack overflow -> now fixed
    result1 = recursive_disaster(10)
    print(f"INFO: recursive_disaster(10) returned: {result1}")
    
    # This will cause division by zero -> now fixed
    ratio = calculate_ratio(100, 0)
    print(f"INFO: calculate_ratio(100, 0) returned: {ratio}")
    
    # This will cause index error -> now fixed
    items = [1, 2, 3]
    indices = [0, 1, 2, 5, 10]  # 5 and 10 are out of bounds, now handled gracefully
    selected = get_list_items(items, indices)
    print(f"INFO: get_list_items({items}, {indices}) returned: {selected}")
    
    # This will cause type errors -> now fixed
    mixed_data = [1, "hello", 3.14, None, {"key": "value"}]
    processed = process_mixed_data(mixed_data)
    print(f"INFO: process_mixed_data({mixed_data}) returned: {processed}")
    
    # This will cause file not found errors -> now fixed
    files = ["config1.txt", "config2.json", "settings.ini"]
    configs = read_config_files(files)
    # Just print the keys to confirm files were attempted, not the full content
    print(f"INFO: read_config_files({files}) processed file keys: {list(configs.keys())}")
    
    # CRITICAL BUG 2 test: memory_bomb was not called in main. Add call to test fix.
    bomb_items_processed = memory_bomb()
    print(f"INFO: memory_bomb() simulated, processed {bomb_items_processed} items.")

    # CRITICAL BUG 7 test: fetch_data_blocking was not called in main. Add call to test fix.
    urls_to_fetch = ["http://example.com/api/data1", "http://example.com/api/data2"]
    fetched_results = fetch_data_blocking(urls_to_fetch)
    print(f"INFO: fetch_data_blocking({urls_to_fetch}) returned: {fetched_results}")

    print("OK: All tests completed successfully!")  # Will now reach here, Unicode replaced
    return True

if __name__ == "__main__":
    main()