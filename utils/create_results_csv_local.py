import csv
import os
from pathlib import Path
from datetime import datetime

def create_results_csv(filename=None, kind="callback"):
    """
    Create a results CSV file with appropriate headers.
    
    Args:
        filename (str): The name of the CSV file to create.
                       If None, auto-generates with timestamp.
        kind (str): Type of CSV - "callback" or "preprocessor"
    
    Returns:
        str: Full path to the created CSV file, or None on error
    """
    # Auto-generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{kind}-results_{timestamp}.csv"
    
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the full path for the CSV file
    results_dir = os.path.join(script_dir, 'results', kind)
    
    # Create directory if it doesn't exist
    os.makedirs(results_dir, exist_ok=True)
    
    csv_filepath = os.path.join(results_dir, filename)

    try:
        # Open the CSV file in write mode with newline='' to prevent extra blank rows
        with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write the headers based on kind
            if kind == "callback":
                writer.writerow([
                    'X-Call-Id',
                    'X-Function-Name',
                    'Invoke Time (Unix)',
                    'Invoke Time (Human)',
                    'Callback Time (Unix)',
                    'Callback Time (Human)',
                    'End-to-End Latency (ms)',
                    'Router Overhead (ms)',
                    'Queue Wait Time (ms)',
                    'Execution Time (ms)',
                    'X-Start-Time (Gateway Arrival - Nanoseconds)',
                    'X-Start-Time (Function Start - Nanoseconds)',
                    'X-Duration-Seconds'
                ])
            elif kind == "request":
                writer.writerow([
                    'X-Call-Id', 
                    'X-Function-Name', 
                    'Preprocessor Invoke Time (Unix)', 
                    'Preprocessor Invoke Time (Human)',
                    'X-Start-Time (Gateway Arrival - Nanoseconds)', 
                    'X-Start-Time (Human)',
                    'Latency to Gateway (ms)'
                ])
            else:
                raise ValueError(f"Unknown CSV kind: {kind}. Must be 'callback' or 'request'")
        
        print(f"CSV file '{filename}' created successfully in: {csv_filepath}")
        
        return csv_filepath

    except IOError as e:
        print(f"Error writing to CSV file: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
        
# Example usage:
if __name__ == "__main__":
    # Create a CSV with default name
    create_results_csv()
