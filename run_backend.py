import os
import sys
import subprocess

def main():
    """
    Wrapper for run_local.py to maintain backward compatibility 
    and ensure unified orchestration.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    run_local_path = os.path.join(script_dir, "run_local.py")
    
    if not os.path.exists(run_local_path):
        print(f"Error: {run_local_path} not found.")
        sys.exit(1)
        
    print("\n[UNIFIED] Redirecting to run_local.py for synchronized backend orchestration...")
    
    # Forward all arguments to run_local.py (though run_local.py currently uses defaults)
    try:
        subprocess.run([sys.executable, run_local_path] + sys.argv[1:], check=True)
    except KeyboardInterrupt:
        pass
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
