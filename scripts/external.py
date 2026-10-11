from pathlib import Path
import json

from src.external_analysis import save_analysis

if __name__ == "__main__":
    print(json.dumps(save_analysis(Path("data/external")), indent=2))
