"""
Test the caching mechanism in system_info.
"""
import sys
sys.path.insert(0, r'c:\Users\kiril\Music\win11_optimizer')

import time

# Test with fresh imports (no cache)
print("=== Test 1: Fresh import (no cache) ===")
import importlib
import system_info
importlib.reload(system_info)

print(f"GPU: {system_info.get_gpu_info()}")
print(f"Motherboard: {system_info.get_motherboard_info()}")

# Test second call (should use cache)
print("\n=== Test 2: Second call (cached) ===")
print(f"GPU: {system_info.get_gpu_info()}")
print(f"Motherboard: {system_info.get_motherboard_info()}")

# Test with delay
print("\n=== Test 3: After 6 second delay (cache expired) ===")
time.sleep(6)
print(f"GPU: {system_info.get_gpu_info()}")
print(f"Motherboard: {system_info.get_motherboard_info()}")

print("\n=== Test Complete ===")
