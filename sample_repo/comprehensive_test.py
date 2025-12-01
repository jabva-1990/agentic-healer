#!/usr/bin/env python3
"""
Comprehensive test file that triggers all the complex bugs we've added.
This will be the main target for our auto-healing system.
"""

import sys
import traceback
import threading
import time
import json
from datetime import datetime

# Import all our buggy modules
try:
    from buggy_module import (
        advanced_calculator, 
        complex_threading_bug,
        complex_data_processing_bugs
    )
    print("✅ Successfully imported buggy_module")
except ImportError as e:
    print(f"❌ Import error in buggy_module: {e}")

try:
    from utils import complex_algorithm_bugs
    print("✅ Successfully imported utils")
except ImportError as e:
    print(f"❌ Import error in utils: {e}")

try:
    from error_test import ComplexDataProcessor
    print("✅ Successfully imported error_test")
except ImportError as e:
    print(f"❌ Import error in error_test: {e}")

def test_calculator_bugs():
    """Test the advanced calculator with various edge cases."""
    print("\n🧮 Testing Advanced Calculator Bugs...")
    
    test_cases = [
        ("3.14", "2", "sqrt"),      # Type conversion + wrong variable bug
        (10, 0, "divide"),          # Division by zero
        (-4, 2, "sqrt"),            # Negative sqrt
        (2, 1001, "power"),         # Memory explosion
        (5, 3, "unknown"),          # Unknown operation
    ]
    
    for x, y, op in test_cases:
        try:
            print(f"  Testing: {x} {op} {y}")
            result = advanced_calculator(x, y, op)
            print(f"    Result: {result}")
        except Exception as e:
            print(f"    ❌ Error: {e}")

def test_threading_bugs():
    """Test complex threading issues."""
    print("\n🧵 Testing Threading Bugs...")
    
    try:
        print("  Starting complex threading operations...")
        result = complex_threading_bug()
        print(f"    Threading completed, result length: {len(result)}")
    except Exception as e:
        print(f"    ❌ Threading error: {e}")
        traceback.print_exc()

def test_data_processing_bugs():
    """Test complex data processing issues."""
    print("\n📊 Testing Data Processing Bugs...")
    
    try:
        print("  Testing data processing with complex scenarios...")
        result = complex_data_processing_bugs("test_data_source")
        print(f"    Data processing result: {result}")
    except Exception as e:
        print(f"    ❌ Data processing error: {e}")
        traceback.print_exc()

def test_algorithm_bugs():
    """Test algorithmic and performance bugs."""
    print("\n⚡ Testing Algorithm Performance Bugs...")
    
    test_scenarios = [
        (list(range(50)), "sort"),
        (list(range(20)), "fibonacci"), 
        (["test", "data", "search"], "search"),
        ([{"id": i, "value": i*2} for i in range(10)], "join")
    ]
    
    for data, algo_type in test_scenarios:
        try:
            print(f"  Testing {algo_type} algorithm with {len(data)} items...")
            start_time = time.time()
            result = complex_algorithm_bugs(data, algo_type)
            end_time = time.time()
            print(f"    ✅ Completed in {end_time - start_time:.3f}s, result size: {len(result) if result else 0}")
        except Exception as e:
            print(f"    ❌ Algorithm error ({algo_type}): {e}")

def test_class_inheritance_bugs():
    """Test complex class and inheritance issues."""
    print("\n🏗️  Testing Class Inheritance Bugs...")
    
    try:
        print("  Creating ComplexDataProcessor with missing config...")
        processor = ComplexDataProcessor("nonexistent_config.json")
        
        # Test with problematic data
        problematic_data = [
            {"value": 10, "multiplier": 2, "offset": 5, "normalizer": 0},  # Division by zero
            {"value": "string", "multiplier": 2, "offset": 1, "normalizer": 1},  # Type error
            {"incomplete": "data"},  # Missing keys
            None,  # Null reference
            42  # Wrong type entirely
        ]
        
        print("  Processing problematic data stream...")
        processor.process_complex_data(problematic_data)
        print("    ✅ Data processing completed")
        
    except Exception as e:
        print(f"    ❌ Class inheritance error: {e}")
        traceback.print_exc()

def stress_test_system():
    """Run a comprehensive stress test."""
    print("\n🚀 Running System Stress Test...")
    
    def cpu_intensive_task(task_id):
        """CPU intensive task that may cause issues."""
        try:
            # Intentionally inefficient computation
            result = 0
            for i in range(100000):
                result += i ** 2
                if i % 50000 == 0:
                    print(f"    Task {task_id}: Progress {i/100000*100:.1f}%")
            return result
        except Exception as e:
            print(f"    ❌ Task {task_id} failed: {e}")
            return None
    
    # Create multiple threads to stress the system
    threads = []
    for i in range(3):
        thread = threading.Thread(target=cpu_intensive_task, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join(timeout=10)  # 10 second timeout
    
    print("    Stress test completed")

def comprehensive_integration_test():
    """Run all tests in sequence."""
    print("🔥 === COMPREHENSIVE BUG TEST SUITE ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    test_results = {}
    
    # Run all test categories
    test_functions = [
        ("Calculator", test_calculator_bugs),
        ("Threading", test_threading_bugs),
        ("Data Processing", test_data_processing_bugs),
        ("Algorithms", test_algorithm_bugs),
        ("Class Inheritance", test_class_inheritance_bugs),
        ("Stress Test", stress_test_system)
    ]
    
    for test_name, test_func in test_functions:
        print(f"\n{'='*50}")
        try:
            test_func()
            test_results[test_name] = "✅ PASSED"
        except Exception as e:
            test_results[test_name] = f"❌ FAILED: {str(e)}"
            print(f"❌ {test_name} failed with: {e}")
    
    # Print summary
    end_time = time.time()
    print(f"\n{'='*50}")
    print("📋 TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(1 for result in test_results.values() if "PASSED" in result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        print(f"{test_name:.<30} {result}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    print(f"Total execution time: {end_time - start_time:.2f} seconds")
    
    # Exit with appropriate code
    if passed < total:
        print("\n⚠️  CRITICAL: System has multiple issues - AUTO-HEALING REQUIRED!")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed - System is healthy!")
        sys.exit(0)

if __name__ == "__main__":
    try:
        comprehensive_integration_test()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected fatal error: {e}")
        traceback.print_exc()
        sys.exit(2)