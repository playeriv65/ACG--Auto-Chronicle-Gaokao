from __future__ import annotations

import os
import subprocess
import sys


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(base_dir, "app.py")

    if not os.path.exists(app_path):
        print(f"Error: Visualizer app not found at {app_path}")
        sys.exit(1)

    print("Launching World Data Visualizer...")
    print(f"Target: {app_path}")

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path], check=True)
    except KeyboardInterrupt:
        print("\nVisualizer stopped.")
    except Exception as e:
        print(f"Error launching visualizer: {e}")


if __name__ == "__main__":
    main()
