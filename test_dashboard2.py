"""
Test dashboard UI update mechanism.
"""
import sys
sys.path.insert(0, r'c:\Users\kiril\Music\win11_optimizer')

# Mock the dashboard behavior
import threading
import time

from system_info import collect_all_async

# Simulate the dashboard's _on_data_ready and _update_ui methods
def test_dashboard_flow():
    print("=== Testing Dashboard Data Flow ===\n")
    
    received_data = None
    
    def on_data_ready(data):
        nonlocal received_data
        received_data = data
        print(f"1. Data received in callback:")
        print(f"   GPU: {data.get('gpu', 'MISSING')}")
        print(f"   Motherboard: {data.get('motherboard', 'MISSING')}")
        update_ui(data)
    
    def update_ui(data):
        print(f"\n2. Updating UI with data:")
        mapping = {
            "ОС": data.get("os", "—"),
            "Процессор": data.get("cpu", "—"),
            "Видеокарта": data.get("gpu", "—"),
            "Материнская плата": data.get("motherboard", "—"),
            "ОЗУ": data.get("ram", "—"),
        }
        for label, value in mapping.items():
            print(f"   {label}: {value}")
    
    # Start async collection
    print("Starting async data collection...\n")
    collect_all_async(on_data_ready)
    
    # Wait for completion
    time.sleep(3)
    
    if received_data:
        print("\n=== SUCCESS: Data flow works correctly ===")
    else:
        print("\n=== FAILED: No data received ===")

if __name__ == "__main__":
    test_dashboard_flow()
