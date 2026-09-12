from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Circuit
from app.utils.circuit_profiles import get_circuit_profile

class CircuitFeatureExtractor:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_features(self, circuit_id: str) -> Dict[str, Any]:
        circuit = await self.db.get(Circuit, circuit_id)
        profile = get_circuit_profile(circuit_id)

        length_km = circuit.length_km if circuit and circuit.length_km else 5.0
        num_corners = circuit.num_corners if circuit and circuit.num_corners else profile.get("num_corners", 16)
        overtaking = profile.get("overtaking_difficulty", 0.5)

        return {
            "circuit_length_km": float(length_km),
            "circuit_overtaking_difficulty": float(overtaking),
            "circuit_num_corners": int(num_corners),
        }
