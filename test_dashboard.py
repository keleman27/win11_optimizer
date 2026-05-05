"""
Test script to diagnose dashboard issues with GPU and motherboard detection.
"""
import sys
sys.path.insert(0, r'c:\Users\kiril\Music\win11_optimizer')

import threading
import time

# Test 1: Direct system_info calls
print("=== Test 1: Direct system_info calls ===")
from system_info import get_gpu_info, get_motherboard_info, collect_all_async

print(f"GPU: {get_gpu_info()}")
print(f"Motherboard: {get_motherboard_info()}")

# Test 2: Async collection
print("\n=== Test 2: Async data collection ===")
result = {}

def callback(data):
    global result
    result = data
    print(f"Received data: {data}")

# Run async collection
collect_all_async(callback)
time.sleep(3)  # Wait for async to complete

print(f"\nGPU from async: {result.get('gpu', 'NOT FOUND')}")
print(f"Motherboard from async: {result.get('motherboard', 'NOT FOUND')}")

print("\n=== All tests completed ===")
