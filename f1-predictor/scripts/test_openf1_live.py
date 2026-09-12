"""Test OpenF1 endpoints live against the real API."""

import urllib.request
import json
import time

BASE = "http://localhost:8000/api/openf1"

def fetch(path):
    url = f"{BASE}/{path}"
    print(f"\n--- GET {url} ---")
    try:
        r = urllib.request.urlopen(url, timeout=30)
        data = json.loads(r.read())
        print(f"  Status: {r.status} | Items: {len(data) if isinstance(data, list) else 'N/A'}")
        if isinstance(data, list) and data:
            print(f"  First item keys: {list(data[0].keys())[:8]}")
        return data
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

# Test meetings
meetings = fetch("meetings?year=2026")
if meetings:
    print(f"\n  2026 Season meetings:")
    for m in meetings[:8]:
        print(f"    {m.get('meeting_name', 'unknown')} | key={m.get('meeting_key')} | country={m.get('country_name')}")

# Test sessions for Spanish GP
print("\n" + "="*70)
print("  SPANISH GP SESSIONS")
print("="*70)
sessions = fetch("sessions?meeting_key=1262&has_data=true")
if sessions:
    for s in sessions:
        print(f"    {s.get('session_name'):<20} | key={s.get('session_key')} | date={s.get('date_start', 'N/A')[:10]}")

# Test laps for the race session
print("\n" + "="*70)
print("  SPANISH GP RACE LAPS (session_key=9877)")
print("="*70)
laps = fetch("laps?session_key=9877&driver_number=44")
if laps:
    print(f"  Hamilton laps: {len(laps)}")
    for lap in laps[:5]:
        print(f"    Lap {lap.get('lap_number')}: {lap.get('lap_duration')}s | S1={lap.get('sector_1_time')} S2={lap.get('sector_2_time')} S3={lap.get('sector_3_time')}")

# Test stints
print("\n" + "="*70)
print("  SPASTINTS (session_key=9877)")
print("="*70)
stints = fetch("stints?session_key=9877")
if stints:
    for stint in stints[:6]:
        print(f"    Driver {stint.get('driver_number')}: {stint.get('tyre_compound')} | laps {stint.get('lap_start')}-{stint.get('lap_end')} | age={stint.get('tyre_age_at_start')}")

# Test pit stops
print("\n" + "="*70)
print("  PIT STOPS (session_key=9877)")
print("="*70)
pits = fetch("pit?session_key=9877")
if pits:
    for pit in pits[:6]:
        print(f"    Driver {pit.get('driver_number')}: lap {pit.get('lap_number')} | lane={pit.get('lane_duration')}s | stop={pit.get('stop_duration')}s")

# Test weather
print("\n" + "="*70)
print("  WEATHER (meeting_key=1262)")
print("="*70)
weather = fetch("weather?meeting_key=1262")
if weather:
    print(f"  Weather observations: {len(weather)}")
    latest = weather[-1] if weather else {}
    print(f"  Latest: Air={latest.get('air_temperature')}C Track={latest.get('track_temperature')}C Humidity={latest.get('humidity')}% Rain={latest.get('rainfall')}")

print("\n\n=== All OpenF1 endpoints tested ===")
