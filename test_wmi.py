"""
Test WMI initialization and GPU/motherboard detection.
"""
import sys
sys.path.insert(0, r'c:\Users\kiril\Music\win11_optimizer')

import time

print("=== WMI Test ===\n")

# Test 1: Direct WMI import and usage
print("Test 1: Direct WMI usage")
try:
    import wmi
    print(f"WMI module imported: {wmi}")
    
    print("Creating WMI client...")
    c = wmi.WMI()
    print(f"WMI client created: {c}")
    
    print("\nQuerying GPU (Win32_VideoController)...")
    gpus = list(c.Win32_VideoController())
    print(f"Found {len(gpus)} GPU(s)")
    for gpu in gpus:
        print(f"  - {gpu.Name} (Driver: {gpu.DriverVersion})")
    
    print("\nQuerying Motherboard (Win32_BaseBoard)...")
    boards = list(c.Win32_BaseBoard())
    print(f"Found {len(boards)} motherboard(s)")
    for board in boards:
        print(f"  - {board.Manufacturer} {board.Product}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")
