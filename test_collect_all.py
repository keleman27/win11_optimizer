"""
Test collect_all_async exactly as dashboard uses it.
"""
import sys
sys.path.insert(0, r'c:\Users\kiril\Music\win11_optimizer')

import threading
import time

print("=== Test: collect_all_async (as dashboard uses) ===\n")

# Import fresh
import importlib
import system_info
importlib.reload(system_info)

results = {}

def my_callback(data):
    """Callback like dashboard's _on_data_ready"""
    print(f"Callback received data (thread: {threading.current_thread().name})")
    print(f"  GPU: {data.get('gpu', 'MISSING')}")
    print(f"  Motherboard: {data.get('motherboard', 'MISSING')}")
    results['data'] = data

print("Starting collect_all_async...")
system_info.collect_all_async(my_callback)

print("Waiting for callback...")
time.sleep(3)

if 'data' in results:
    print("\n=== SUCCESS ===")
else:
    print("\n=== FAILED: No callback received ===")
