#!/usr/bin/env python3
"""Fetch latest AROW telemetry from public GCS bucket p-2-cen1 and parse it.

Usage: python arow_gcs_fetch.py
"""
import json
import urllib.request
import urllib.error
from datetime import datetime
from urllib.parse import quote_plus

BUCKET = "p-2-cen1"
LIST_URL = f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o?maxResults=200"


def list_objects():
    try:
        with urllib.request.urlopen(LIST_URL, timeout=15) as r:
            data = json.load(r)
            return data.get("items", [])
    except urllib.error.HTTPError as e:
        print("HTTP Error listing bucket:", e)
        return []
    except Exception as e:
        print("Error listing bucket:", e)
        return []


def pick_latest(items):
    # Prefer plain telemetry files (txt/json) and recent updated timestamp
    if not items:
        return None
    # Filter by likely telemetry file extensions
    cand = [it for it in items if it.get("name", "").lower().endswith(('.txt', '.json'))]
    if not cand:
        cand = items
    cand.sort(key=lambda it: it.get("updated", ""), reverse=True)
    return cand[0]


def fetch_object(name):
    # Try the raw path first, then an encoded path
    url_raw = f"https://storage.googleapis.com/{BUCKET}/{name}"
    url_enc = f"https://storage.googleapis.com/{BUCKET}/{quote_plus(name)}"
    for u in (url_raw, url_enc):
        try:
            with urllib.request.urlopen(u, timeout=15) as r:
                # read as text
                data = r.read()
                try:
                    return data.decode("utf-8")
                except Exception:
                    return data.decode("latin-1", errors="replace")
        except urllib.error.HTTPError as e:
            # 404 or others
            # continue to next
            continue
        except Exception:
            continue
    return None


def parse_telemetry(text):
    # Many files are JSON objects; try to load
    try:
        d = json.loads(text)
    except Exception:
        # Try to find a JSON object inside text
        import re

        m = re.search(r"\{[\s\S]*\}\s*$", text)
        if m:
            try:
                d = json.loads(m.group(0))
            except Exception:
                return None
        else:
            return None

    # Check for Parameter_ keys
    keys = d.keys()
    for k in ("Parameter_2003", "Parameter_2004", "Parameter_2005"):
        if k not in d:
            # not recognized telemetry structure
            break
    else:
        try:
            x = float(d["Parameter_2003"]["Value"])
            y = float(d["Parameter_2004"]["Value"])
            z = float(d["Parameter_2005"]["Value"])
            vx = float(d.get("Parameter_2009", {}).get("Value", 0))
            vy = float(d.get("Parameter_2010", {}).get("Value", 0))
            vz = float(d.get("Parameter_2011", {}).get("Value", 0))
            # Units in feet for position and ft/s for velocity (per AROW JS)
            # convert to km and km/h
            ft_to_km = 0.0003048
            pos_km = (x * ft_to_km, y * ft_to_km, z * ft_to_km)
            r_km = (pos_km[0] ** 2 + pos_km[1] ** 2 + pos_km[2] ** 2) ** 0.5
            altitude_km = r_km - 6371.0
            speed_kmh = ( (vx**2 + vy**2 + vz**2) ** 0.5 ) * ft_to_km * 3600.0
            return {
                "pos_km": pos_km,
                "range_from_center_km": r_km,
                "altitude_km": altitude_km,
                "speed_kmh": speed_kmh,
                "raw": d,
            }
        except Exception:
            return None
    return None


def main():
    print("Listing bucket", BUCKET)
    items = list_objects()
    print("Objects listed:", len(items))
    latest = pick_latest(items)
    if not latest:
        print("No objects found")
        return 1
    name = latest.get("name")
    updated = latest.get("updated")
    size = latest.get("size")
    print("Picked:", name, updated, size)

    txt = fetch_object(name)
    if not txt:
        print("Failed to fetch object")
        return 2
    print("Fetched", len(txt), "bytes; parsing...")
    parsed = parse_telemetry(txt)
    if not parsed:
        print("Telemetry parse failed or not recognized. Showing raw snippet:\n")
        print(txt[:2000])
        return 3

    print("Parsed telemetry:")
    print("  Altitude (km):", round(parsed['altitude_km'], 3))
    print("  Range (km from center):", round(parsed['range_from_center_km'], 3))
    print("  Speed (km/h):", round(parsed['speed_kmh'], 3))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
