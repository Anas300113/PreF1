#!/usr/bin/env python3
"""Train ML models from ingested historical data (chronological, leakage-safe)."""
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import get_settings
from app.database import AsyncSessionLocal, init_db
from app.ml.dnf_model import DNFModel
from app.ml.model_registry import ModelRegistry
from app.ml.qualifying_model import QualifyingModel
from app.ml.race_pace_model import RacePaceModel
from app.ml.training_data_builder import TrainingDataBuilder
from app.ml.validation import chronological_split
from app.utils.logging_config import setup_logging

setup_logging("INFO")
settings = get_settings()


async def main():
    print("Training PreF1 ML pipeline from historical database...")
    await init_db()

    async with AsyncSessionLocal() as session:
        builder = TrainingDataBuilder(session)

        X_quali, y_quali = await builder.build_qualifying_dataset(2018, 2024)
        X_pace, y_pace = await builder.build_race_pace_dataset(2018, 2024)
        X_dnf, y_dnf = await builder.build_dnf_dataset(2018, 2024)

        if X_quali.empty or len(X_quali) < 50:
            print(
                f"WARNING: Insufficient training data ({len(X_quali)} qualifying samples). "
                "Run scripts/ingest_historical.py first."
            )
            if X_quali.empty:
                print("Aborting — no data to train on.")
                return

        registry = ModelRegistry(settings.models_dir)
        cutoff = datetime.now(timezone.utc).isoformat()

        # Qualifying model
        q_train, q_val = chronological_split(X_quali, y_quali, val_fraction=0.15)
        q_model = QualifyingModel()
        q_model.train(q_train[0], q_train[1], q_val[0], q_val[1])
        registry.save_model(q_model, "qualifying", "v1.0", {
            "training_samples": len(X_quali),
            "training_cutoff": cutoff,
            "target": "gap_to_pole_s",
        })
        print(f"Qualifying model trained on {len(X_quali)} samples")

        # Race pace model
        p_train, p_val = chronological_split(X_pace, y_pace, val_fraction=0.15)
        r_model = RacePaceModel()
        r_model.train(p_train[0], p_train[1])
        registry.save_model(r_model, "race_pace", "v1.0", {
            "training_samples": len(X_pace),
            "training_cutoff": cutoff,
            "target": "race_pace_index",
        })
        print(f"Race pace model trained on {len(X_pace)} samples")

        # DNF model
        d_model = DNFModel()
        d_model.train(X_dnf, y_dnf)
        registry.save_model(d_model, "dnf", "v1.0", {
            "training_samples": len(X_dnf),
            "training_cutoff": cutoff,
            "target": "binary_dnf",
            "positive_rate": float(y_dnf.mean()),
        })
        print(f"DNF model trained on {len(X_dnf)} samples")

    print("All models saved to", settings.models_dir)


if __name__ == "__main__":
    asyncio.run(main())
