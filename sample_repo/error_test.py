#!/usr/bin/env python3
"""
Corrected Python script with various fixes.
Original intent (misleadingly named 'test file') has been preserved as a script.
"""

import os
import json
# import requests  # This import was unused and has been removed to avoid unnecessary dependencies and potential ImportError.

class ComplexDataProcessor:  # Enhanced with complex error scenarios
    """
    Class with complex error handling bugs and edge cases.
    """
    
    def __init__(self, config_path=None):
        self.data = []
        self.results = None
        self.config = {}
        
        # Bug 1: Swallowing all exceptions without proper handling
        try:
            if config_path:
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
        except:
            pass  # Silent failure - very bad!
        
        # Bug 2: Assuming config keys exist without validation
        self.max_items = self.config['max_items']  # KeyError if not in config
        self.timeout = self.config.get('timeout', 30)
    
    def process_complex_data(self, data_stream):
        """Process data with complex error scenarios."""
        
        # Bug 3: Exception handling with wrong exception types
        try:
            for item in data_stream:
                # Complex processing that can fail in multiple ways
                processed = self._complex_transform(item)
                self.data.append(processed)
                
        except ValueError as e:
            # Bug: Catching ValueError but the function raises TypeError
            print(f"Value error occurred: {e}")
            return None
        except Exception as e:
            # Bug: Too broad exception handling
            print("Some error occurred")
            # Bug: Not re-raising or handling properly
            self.data = []  # Lost all data!
        
        # Bug 4: Finally block with side effects
        finally:
            # Bug: Modifying state in finally block
            self.data = self.data[:100]  # Truncating data unexpectedly
    
    def _complex_transform(self, item):
        """Transform item with multiple failure points."""
        
        # Bug 5: Chain of operations without intermediate validation
        try:
            # This chain will fail if item is None, not dict, or missing keys
            result = item['value'] * item['multiplier'] + item['offset']
            
            # Bug 6: Division without checking for zero
            normalized = result / item['normalizer']  # ZeroDivisionError
            
            # Bug 7: Type assumptions without validation
            return normalized.upper()  # AttributeError if normalized is not string
            
        except KeyError:
            # Bug: Returning different types in error cases
            return "ERROR"  # Should return same type or raise
        except ZeroDivisionError:
            # Bug: Magic number without explanation
            return 99999  # What does this mean?
        # Bug: Not handling AttributeError or TypeError
    
    def __init__(self):
        self.data = []
        self.results = None
    
    def process_items(self, items):
        """Process items. Multiplies positive items by 2, others become 0."""
        processed_data = [] # Using a temporary list for processing for clarity
        for item in items:
            if item > 0: # FIX: Added missing colon here
                processed_data.append(item * 2)
            else:
                processed_data.append(0)
        self.data = processed_data # Update instance data after processing
        return self.data
    
    def save_results(self, filename):
        """
        Save results to file with proper error handling.
        FIX: Added try-except block for robust file operations.
        """
        try:
            # Ensure the directory exists if needed, though 'w' mode typically handles file creation.
            # For robustness, consider: os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(self.data, f, indent=4) # Added indent for readability in JSON output
            print(f"Results successfully saved to '{filename}'")
        except IOError as e:
            print(f"Error: Could not save results to '{filename}'. Reason: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while saving results: {e}")
        # FIX: Removed misleading comment '# Missing closing parenthesis' as no such error existed.
        
def calculate_average(numbers):
    """
    Calculate the average of a list of numbers.
    FIX: Added a check for an empty list to prevent ZeroDivisionError.
    """
    if not numbers:
        print("Warning: Attempted to calculate average of an empty list. Returning 0.0.")
        return 0.0 # Returning 0.0 is a common convention for the average of an empty set.
                   # Alternatively, one might raise a ValueError or return None depending on requirements.
    return sum(numbers) / len(numbers)

def main():
    processor = DataProcessor()
    test_data = [1, 2, -1, 4, 0]
    
    results = processor.process_items(test_data)
    print(f"Processed data: {results}") # Added print for processed data visibility
    
    avg = calculate_average(results)
    
    print(f"Average: {avg}")
    processor.save_results("output.json")

if __name__ == "__main__":
    main()