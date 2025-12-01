#!/usr/bin/env python3
"""
Main application file with intentional issues for self-healing agent testing.
"""

import logging

def process_data(data_list):
    """Process a list of data items with logging for detailed tracking."""
    # FIX: Added missing closing parenthesis to the logging.info statement. (This fix was applied in a previous iteration)
    logging.info(f"Starting to process {len(data_list)} items")
    
    results = []
    
    # Get the logger instance and check if DEBUG level is enabled once before the loop.
    # This avoids repeated calls to getLogger() and isEnabledFor() inside the tight loop,
    # minimizing overhead even further when debug logs are suppressed.
    logger = logging.getLogger()
    is_debug_enabled = logger.isEnabledFor(logging.DEBUG)

    for i, item in enumerate(data_list):
        # Guard DEBUG logging statements to prevent f-string evaluation and
        # function call overhead when DEBUG level is not active.
        if is_debug_enabled:
            logging.debug(f"Processing item {i}: {item}") 
        
        # Simulate some processing - removed blocking time.sleep for performance improvement
        # (This fix was applied in a previous iteration)
        processed_item = str(item).upper() # Ensures item is string before .upper(), preventing AttributeError
        results.append(processed_item)
        
        # Guard DEBUG logging statements for performance
        if is_debug_enabled:
            logging.debug(f"Processed: {processed_item}")
    
    logging.info("Processing complete!")
    return results

def main():
    """Main function demonstrating data processing with logging."""
    logging.info("Application starting...")
    
    # Sample data
    sample_data = ["hello", "world", "python", "healing", "agent"]
    
    # Process data (this will be slow due to sleep, now improved)
    results = process_data(sample_data)
    
    # Display results with more logs - Modified for performance to avoid logging each item if results list is very large
    # (This fix was applied in a previous iteration)
    logging.info(f"Processing complete. Total items processed: {len(results)}")
    # Log a sample of results rather than all to prevent I/O bottleneck for large datasets
    if results: # Check if results list is not empty before attempting to slice
        logging.info(f"Sample of processed results (first 3): {results[:3]}")
    if len(results) > 3: # Only log last 3 if there are more than 3 items total to avoid redundancy for small lists
        logging.info(f"Sample of processed results (last 3): {results[-3:]}")
    
    logging.info("Application finished successfully!")
    return results

if __name__ == "__main__":
    # Configure logging at the start of the application's execution block
    # By default, INFO messages and above will be shown. DEBUG messages will be suppressed.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()