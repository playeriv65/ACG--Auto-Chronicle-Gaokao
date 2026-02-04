import os
import subprocess
import sys

def main():
    # Path to the streamlit app
    # This script is at novel_engine/data/visualizer/launch.py
    # app is at novel_engine/data/visualizer/app.py
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_PATH = os.path.join(BASE_DIR, "app.py")
    
    if not os.path.exists(APP_PATH):
        print(f"Error: Visualizer app not found at {APP_PATH}")
        sys.exit(1)
        
    print(f"Launching World Data Visualizer...")
    print(f"Target: {APP_PATH}")
    
    try:
        # We run streamlit as a module
        subprocess.run([sys.executable, "-m", "streamlit", "run", APP_PATH], check=True)
    except KeyboardInterrupt:
        print("\nVisualizer stopped.")
    except Exception as e:
        print(f"Error launching visualizer: {e}")

if __name__ == "__main__":
    main()
