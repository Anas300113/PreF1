import json, os
from pathlib import Path
from typing import Dict, Any, Optional

class ModelRegistry:
    def __init__(self, models_dir: str = "./models/trained"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = self.models_dir / "metadata"
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    def save_model(self, model_obj: Any, model_type: str, version: str, metadata: Dict[str, Any]) -> str:
        model_path = self.models_dir / f"{model_type}_{version}.joblib"
        meta_path = self.meta_dir / f"{model_type}_{version}.json"

        if hasattr(model_obj, "save"):
            model_obj.save(str(model_path))
        
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return str(model_path)

    def get_metadata(self, model_type: str, version: str) -> Optional[Dict[str, Any]]:
        meta_path = self.meta_dir / f"{model_type}_{version}.json"
        if not meta_path.exists():
            return None
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_models(self) -> Dict[str, list]:
        models = {}
        for f in self.meta_dir.glob("*.json"):
            parts = f.stem.split("_")
            m_type = parts[0]
            models.setdefault(m_type, []).append(f.name)
        return models
