#!/usr/bin/env python3
"""Ingest lap timing and tyre stint data from OpenF1 for feature enrichment.

OpenF1 provides lap times with sector times, speed traps, and tyre stint data
from the 2023 season onwards. Use this to enrich the ML features for better
quali and race-pace predictions.

Usage:
    python scripts/ingest_openf1.py --year 2025 --meeting 1262
    python scripts/ingest_openf1.py --session 9877
    python scripts/ingest_openf1.py --latest --race-only

Rate limit: 3 req/s, 30 req/min (free tier, no API key).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import get_settings
from app.services.openf1_client import OpenF1Client


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest OpenF1 lap & stint data")
    parser.add_argument("--year", type=int, help="Season year")
    parser.add_argument("--meeting", type=int, help="Meeting key (race weekend)")
    parser.add_argument("--session", type=int, help="Session key")
    parser.add_argument("--latest", action="store_true", help="Use latest meeting")
    parser.add_argument("--race-only", action="store_true", help="Only ingest race session")
    parser.add_argument("--output", type=str, default="data/cache/openf1", help="Output directory")
    args = parser.parse_args()

    settings = get_settings()
    client = OpenF1Client(settings)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    meeting_key = args.meeting

    if args.latest:
        print("Fetching latest meeting...")
        meeting = client.get_latest_meeting()
        if not meeting:
            print("No latest meeting found")
            return
        meeting_key = meeting["meeting_key"]
        print(f"Latest meeting: {meeting.get('meeting_name')} (key={meeting_key})")

    if args.session:
        session_key = args.session
    elif meeting_key:
        print(f"Fetching sessions for meeting {meeting_key}...")
        sessions = client.get_sessions(meeting_key=meeting_key, has_data=True)
        if not sessions:
            print("No sessions found")
            return

        if args.race_only:
            race_sessions = [s for s in sessions if s.get("session_name") == "Race"]
            if not race_sessions:
                print("No race session found")
                return
            target_sessions = race_sessions
        else:
            target_sessions = sessions

        for s in target_sessions:
            session_key = s["session_key"]
            session_name = s.get("session_name", "unknown")
            print(f"\nIngesting {session_name} (session_key={session_key})...")

            # Laps
            print("  Fetching laps...")
            laps = client.get_laps(session_key=session_key)
            if laps:
                lap_file = output_dir / f"laps_{session_key}.json"
                lap_file.write_text(json.dumps(laps, indent=2), encoding="utf-8")
                print(f"    Saved {len(laps)} laps to {lap_file}")

            # Stints
            print("  Fetching stints...")
            stints = client.get_stints(session_key=session_key)
            if stints:
                stint_file = output_dir / f"stints_{session_key}.json"
                stint_file.write_text(json.dumps(stints, indent=2), encoding="utf-8")
                print(f"    Saved {len(stints)} stints to {stint_file}")

            # Pit stops
            print("  Fetching pit stops...")
            pits = client.get_pit_stops(session_key=session_key)
            if pits:
                pit_file = output_dir / f"pit_{session_key}.json"
                pit_file.write_text(json.dumps(pits, indent=2), encoding="utf-8")
                print(f"    Saved {len(pits)} pit stops to {pit_file}")

            # Weather (per meeting, not per session)
            if target_sessions[0] == s:
                print("  Fetching weather...")
                weather = client.get_weather(meeting_key=meeting_key)
                if weather:
                    weather_file = output_dir / f"weather_{meeting_key}.json"
                    weather_file.write_text(json.dumps(weather, indent=2), encoding="utf-8")
                    print(f"    Saved {len(weather)} weather observations to {weather_file}")

            time.sleep(0.5)  # Respect rate limit
    else:
        print("Must specify --meeting, --session, or --latest")
        return

    print("\nIngestion complete.")


if __name__ == "__main__":
    main()
