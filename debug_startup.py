import sys
import os
import time

print("DIAGNOSTIC: Starting import check...")
try:
    print("STEP 1: Importing flwr...")
    import flwr as fl
    print("STEP 1: Success.")

    print("STEP 2: Importing torch...")
    import torch
    print("STEP 2: Success.")

    print("STEP 3: Adding project root to path...")
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
    print(f"STEP 3: PYTHONPATH set to {cwd}")

    print("STEP 4: Importing Cybronites.server.bridge...")
    from Cybronites.server.bridge import bridge
    print("STEP 4: Success.")

    print("STEP 5: Importing Cybronites.server.server...")
    from Cybronites.server.server import main
    print("STEP 5: Success.")

    print("DIAGNOSTIC: All imports successful. Attempting to start bridge components...")
    
except Exception as e:
    print(f"DIAGNOSTIC ERROR: {e}")
    import traceback
    traceback.print_exc()

print("DIAGNOSTIC: Finished.")
