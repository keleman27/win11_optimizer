"""
Test WMI in a background thread (like dashboard does).
"""
import sys
sys.path.insert(0, r'c:\Users\kiril\Music\win11_optimizer')

import threading
import time

results = {}

def worker():
    """Run system_info in a background thread."""
    print(f"Worker thread: {threading.current_thread().name}")
    
    # Import inside thread
    from system_info import get_gpu_info, get_motherboard_info
    
    try:
        gpu = get_gpu_info()
        print(f"  GPU result: {gpu}")
        results['gpu'] = gpu
    except Exception as e:
        print(f"  GPU error: {e}")
        results['gpu_error'] = str(e)
    
    try:
        mb = get_motherboard_info()
        print(f"  Motherboard result: {mb}")
        results['motherboard'] = mb
    except Exception as e:
        print(f"  Motherboard error: {e}")
        results['mb_error'] = str(e)

print("=== Test: WMI in Background Thread ===\n")

# Run in main thread first
print("Main thread test:")
from system_info import get_gpu_info, get_motherboard_info
print(f"  GPU: {get_gpu_info()}")
print(f"  Motherboard: {get_motherboard_info()}")

# Now run in background thread
print("\nBackground thread test:")
t = threading.Thread(target=worker, daemon=True)
t.start()
t.join(timeout=10)

print(f"\nResults from thread: {results}")

if 'gpu_error' in results or 'mb_error' in results:
    print("\n=== ISSUE FOUND: WMI fails in background thread ===")
else:
    print("\n=== Thread test passed ===")
