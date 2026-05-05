#!/usr/bin/env python3
"""
Test script to verify the application starts without callback errors.
"""

import sys
import traceback
import threading
import time

def test_import():
    """Test if all modules can be imported successfully."""
    try:
        import main
        print("✓ All modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """Test if the application can be created without hanging."""
    try:
        import customtkinter as ctk
        from main import App
        
        # Create a test root window
        root = ctk.CTk()
        root.withdraw()  # Hide the window during testing
        
        # Test app creation
        app = App()
        print("✓ App created successfully")
        
        # Schedule window close after a short delay
        root.after(2000, root.quit)
        
        # Start the event loop briefly
        root.mainloop()
        
        # Cleanup
        try:
            from system_sync import sync_engine
            sync_engine.unregister_all()
        except:
            pass
            
        print("✓ App test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ App creation error: {e}")
        traceback.print_exc()
        return False

def main():
    print("Testing Win11 Optimizer startup...")
    print("=" * 50)
    
    # Test imports
    if not test_import():
        return False
    
    # Test app creation with timeout
    print("\nTesting app creation...")
    result = test_app_creation()
    
    if result:
        print("\n✓ All tests passed! The application should start without hanging.")
        return True
    else:
        print("\n✗ Tests failed. There may still be callback issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
