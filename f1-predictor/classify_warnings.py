import re

path = "pytest9.log"
text = open(path, encoding="utf-16", errors="replace").read()
lines = text.split(chr(10))
pat = re.compile(r"^(.*?):(\d+):\s*([A-Z][A-Za-z]*):\s*(.*)$")
counts = {}

for i, line in enumerate(lines):
    m = pat.match(line)
    if m:
        source = m.group(1).rsplit(chr(92))[-1]
        cat = m.group(3)
        repo = source if not source.startswith((".", "_")) else "site-packages"
        key = (repo, cat)
        counts[key] = counts.get(key, 0) + 1

print("TOTAL classified warning lines:", sum(counts.values()))
print()
for (src, cat), n in sorted(counts.items(), key=lambda kv: -kv[1])[:30]:
    print(f"{n:5d}  {src:34s} {cat}")
