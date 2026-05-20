#!/usr/bin/env python3
# epub-translator-toolkit
# Author: wangxu  |  Version: 0.0.1  |  2026-05-20 00:39
import sys, json, os

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return

    mode = sys.argv[1]
    path = sys.argv[2]

    if mode == "extract":
        start, end = int(sys.argv[3]), int(sys.argv[4])
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        batch = [e for e in data if start <= e["idx"] < end]
        out_path = f"batch_{start}_{end}.txt"
        with open(out_path, 'w', encoding='utf-8') as f:
            for e in batch:
                f.write(f"[{e['idx']}] {e['text']}\n\n")
        chars = sum(len(e["text"]) for e in batch)
        print(f"Extracted {len(batch)} segments ({chars} chars) -> {out_path}")
        map_path = out_path.replace('.txt', '_translated.json')
        print(f"Create {map_path} with format: {{\"0\": \"translation\", ...}}")

    elif mode == "inject":
        map_path = sys.argv[3]
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(map_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        updated = 0
        for e in data:
            key = str(e["idx"])
            if key in mapping and mapping[key]:
                e["translated"] = mapping[key]
                updated += 1
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Injected {updated} translations -> {path}")

    elif mode == "info":
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        total = len(data)
        done = sum(1 for e in data if e.get("translated"))
        total_chars = sum(len(e["text"]) for e in data)
        done_chars = sum(len(e["translated"]) for e in data if e.get("translated"))
        print(f"Segments: {total}")
        print(f"Translated: {done} ({done*100//total}%)")
        print(f"Source: {total_chars} chars -> Translation: {done_chars} chars")
        by_file = {}
        for e in data:
            f = e["file"]
            by_file.setdefault(f, {"t": 0, "d": 0})
            by_file[f]["t"] += 1
            if e.get("translated"):
                by_file[f]["d"] += 1
        for f, s in sorted(by_file.items()):
            bar_len = 20
            filled = s["d"] * bar_len // s["t"] if s["t"] else 0
            bar = "#" * filled + "-" * (bar_len - filled)
            print(f"  {f}: [{bar}] {s['d']}/{s['t']}")

    else:
        print(f"Unknown mode: {mode}")
        print(__doc__)

if __name__ == "__main__":
    main()
