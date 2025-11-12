"""Launch the Streamlit UI for LinkedIn to Notion migration tool."""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    app_path = Path(__file__).parent.parent / "src" / "linkedin_notion_migrator" / "app.py"
    
    if not app_path.exists():
        print(f"Error: Streamlit app not found at {app_path}")
        sys.exit(1)
    
    print(f"Launching Streamlit UI from {app_path}")
    subprocess.run(["streamlit", "run", str(app_path)])
