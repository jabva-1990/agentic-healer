import sys
import random

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def load_data(self, filename):
        # Issue: File handling without proper error checking
        file = open(filename, 'r')
        self.data = file.read().split('\n')
        file.close()
    
    def process_items(self):
        # Issue: List index out of range potential
        results = []
        for i in range(len(self.data) + 1):  # Off by one error
            if self.data[i].strip():
                results.append(self.data[i].upper())
        return results
    
    def calculate_stats(self):
        # Issue: Division by zero
        total = sum([len(item) for item in self.data])
        return total / len(self.data)

def helper_function(x, y):
    # Issue: Unreachable code
    if x > y:
        return x + y
    else:
        return x - y
    print("This will never execute")  # Dead code

# Issue: Global variable assignment
global_counter = 0

def increment_counter():
    global global_counter
    global_counter += 1
    return global_counter