#!/usr/bin/env python3
"""Monthly climate normals from Open-Meteo's historical archive (last three full years).

Usage: climate.py "name lat lng" ["name lat lng" ...]
Prints hi/lo/rain arrays ready to paste into data.js `climate`.
"""
import json, sys, urllib.request, datetime

def normals(lat, lng):
    y = datetime.date.today().year
    url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lng}"
           f"&start_date={y-3}-01-01&end_date={y-1}-12-31"
           "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto")
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.load(r)["daily"]
    mx, mn, pr = [[] for _ in range(12)], [[] for _ in range(12)], [[] for _ in range(12)]
    for t, a, b, p in zip(d["time"], d["temperature_2m_max"], d["temperature_2m_min"], d["precipitation_sum"]):
        m = int(t[5:7]) - 1
        if a is not None: mx[m].append(a)
        if b is not None: mn[m].append(b)
        if p is not None: pr[m].append(p)
    avg = lambda l: round(sum(l) / len(l), 1) if l else None
    return [avg(x) for x in mx], [avg(x) for x in mn], [round(sum(x) / 3) for x in pr]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        name, lat, lng = arg.split()
        hi, lo, rain = normals(float(lat), float(lng))
        print(f"// {name}\nclimate: {{ hi: {hi}, lo: {lo}, rain: {rain} }},")
