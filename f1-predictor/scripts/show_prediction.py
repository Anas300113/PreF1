import urllib.request
import json

r = urllib.request.urlopen('http://localhost:8000/api/races/2026_14/prediction?sim_count=50000&seed=42', timeout=120)
data = json.loads(r.read())

drivers = sorted(data['drivers'], key=lambda d: d['win_probability'], reverse=True)

print('=' * 95)
print('  SPANISH GRAND PRIX — Madring, Madrid — 2026-09-13')
print('=' * 95)
print(f'  Model: {data["model"]["version"]}  |  Simulations: {data["model"]["simulation_count"]:,}  |  Runtime: {data["model"]["runtime_seconds"]:.2f}s')
print(f'  Weather: {data["weather"]["temperature_c"]}C  |  Wet: {data["weather"]["is_wet"]}  |  Rain prob: {data["weather"]["precipitation_probability"]}%')
print(f'  Convergence: {data.get("convergence_report", "N/A")}')

# Also show the raw keys for debugging
print(f'  Response keys: {list(data.keys())}')
print('-' * 95)
print(f'  {"#":>2} {"Driver":<22} {"Team":<20} {"Win%":>6} {"Pod%":>6} {"Top5":>6} {"Pts":>5} {"DNF":>5} {"Pts":>5} {"Med":>4}')
print('-' * 95)
for i, d in enumerate(drivers, 1):
    print(f'  {i:>2} {d["full_name"]:<22} {d["team"]:<20} '
          f'{d["win_probability"]*100:>5.1f} {d["podium_probability"]*100:>5.1f} '
          f'{d["top5_probability"]*100:>5.1f} {d["points_probability"]*100:>4.1f} '
          f'{d["dnf_probability"]*100:>4.1f} {d["expected_points"]:>5.1f} '
          f'{d["median_position"]:>4.0f}')
print('-' * 95)

# Qualifying prediction
quali = sorted(data.get('qualifying_prediction', []), key=lambda q: q.get('expected_position', 99))
if quali:
    print()
    print('  PREDICTED QUALIFYING ORDER:')
    print('-' * 50)
    for i, q in enumerate(quali[:10], 1):
        print(f'  P{i}: {q.get("code", "?")} ({q.get("driver_id", "?")})')

# Top pairwise comparisons
pairwise = data.get('pairwise_finish_matrix', {})
if pairwise:
    print()
    print('  KEY HEAD-TO-HEAD (P(row beats column)):')
    top3 = [d['driver_id'] for d in drivers[:3]]
    print(f'       {"  ".join(f" {t[:3]:>3}" for t in top3)}')
    for di in top3:
        row = []
        for dj in top3:
            if di == dj:
                row.append('  - ')
            else:
                row.append(f'{pairwise.get(di, {}).get(dj, 0.5)*100:>4.0f}')
        print(f'  {di[:3]:>3} [{"  ".join(row)}]')

print()
print(f'  {data["disclaimer"]}')
