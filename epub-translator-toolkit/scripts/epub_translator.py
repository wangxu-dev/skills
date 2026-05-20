#!/usr/bin/env python3
# epub-translator-toolkit
# Author: wangxu  |  Version: 0.0.1  |  2026-05-20 00:39
# License: MIT
import os, sys, json, zipfile, re, tempfile
from pathlib import Path
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

BLOCK_TAGS = {
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'li', 'td', 'th', 'div', 'span', 'a',
    'dt', 'dd', 'blockquote', 'label', 'caption',
}

def _is_in_code(element):
    p = element.parent if hasattr(element, 'parent') else element
    while p is not None:
        if p.name in ('code', 'pre', 'script', 'style', 'svg', 'math'):
            return True
        p = p.parent if hasattr(p, 'parent') else None
    return False

def _walk_text(block, parts, code_map, code_idx, all_nodes):
    for child in block.children:
        if isinstance(child, str):
            text = child.strip()
            if text:
                parts.append(text)
                all_nodes.append(("text", child))
        elif child.name == 'code':
            placeholder = f"⌜CODE_{code_idx[0]}⌝"
            code_map[placeholder] = str(child)
            code_idx[0] += 1
            parts.append(placeholder)
            all_nodes.append(("code", child))
        elif child.name not in ('script', 'style'):
            _walk_text(child, parts, code_map, code_idx, all_nodes)

def _extract_block_text(block):
    code_map = {}
    code_idx = [0]
    parts = []
    all_nodes = []
    _walk_text(block, parts, code_map, code_idx, all_nodes)
    plain_text = re.sub(r'\s+', ' ', ' '.join(parts)).strip()
    return plain_text, code_map, all_nodes

def extract_and_export(epub_path, output_json):
    tmpdir = tempfile.mkdtemp(prefix="epub_")
    extract_to = os.path.join(tmpdir, "extracted")
    print(f"Extracting {epub_path}...")
    with zipfile.ZipFile(epub_path, 'r') as z:
        z.extractall(extract_to)
    html_files = []
    for root, _, names in os.walk(extract_to):
        for n in names:
            if n.endswith(('.html', '.xhtml', '.htm')):
                html_files.append(os.path.join(root, n))
    html_files.sort()
    entries = []
    idx = 0
    for html_path in html_files:
        rel = os.path.relpath(html_path, extract_to)
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        for block in soup.find_all(BLOCK_TAGS):
            if _is_in_code(block):
                continue
            has_block_children = any(
                child.name in BLOCK_TAGS for child in block.children
                if hasattr(child, 'name') and child.name
            )
            if has_block_children:
                continue
            text, code_map, _ = _extract_block_text(block)
            if not text:
                continue
            entries.append({
                "idx": idx, "file": rel, "text": text,
                "code_map": code_map, "translated": None,
            })
            idx += 1
    for root, _, files in os.walk(extract_to):
        for f in files:
            if f.endswith('.ncx'):
                ncx_path = os.path.join(root, f)
                rel = os.path.relpath(ncx_path, extract_to)
                with open(ncx_path, 'r', encoding='utf-8') as nf:
                    ncx_content = nf.read()
                for text_match in re.finditer(r'<text>(.*?)</text>', ncx_content):
                    t = text_match.group(1).strip()
                    if t:
                        entries.append({
                            "idx": idx, "file": rel, "text": t,
                            "code_map": {}, "translated": None,
                        })
                        idx += 1
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    total_chars = sum(len(e["text"]) for e in entries)
    print(f"Exported {len(entries)} segments, {total_chars} chars -> {output_json}")
    meta = {"extract_dir": extract_to}
    with open(output_json + ".meta.json", 'w') as f:
        json.dump(meta, f)
    print(f"\nNext: translate segments, then run:")
    print(f"  python scripts/epub_translator.py build <source.epub> {output_json}")

def inject_and_build(epub_path, translation_json, output_epub):
    with open(translation_json, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    meta_path = translation_json + ".meta.json"
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        extract_to = meta["extract_dir"]
    else:
        tmpdir = tempfile.mkdtemp(prefix="epub_")
        extract_to = os.path.join(tmpdir, "extracted")
        with zipfile.ZipFile(epub_path, 'r') as z:
            z.extractall(extract_to)
    total = len(entries)
    done = sum(1 for e in entries if e["translated"] is not None)
    print(f"Progress: {done}/{total} ({done * 100 // total}%)")
    if done < total:
        print(f"Warning: {total - done} segments untranslated — originals preserved.")
    by_file = {}
    for e in entries:
        if e["translated"] is None:
            continue
        by_file.setdefault(e["file"], []).append(e)
    for rel_path, segs in by_file.items():
        file_path = os.path.join(extract_to, rel_path)
        if not os.path.exists(file_path):
            print(f"  File not found: {file_path}")
            continue
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        block_idx = 0
        for block in soup.find_all(BLOCK_TAGS):
            if _is_in_code(block):
                continue
            text, _, _ = _extract_block_text(block)
            if not text:
                continue
            has_block_children = any(
                child.name in BLOCK_TAGS for child in block.children
                if hasattr(child, 'name') and child.name
            )
            if has_block_children:
                continue
            if block_idx < len(segs):
                seg = segs[block_idx]
                if seg["translated"]:
                    translated = seg["translated"]
                    for placeholder, code_html in seg.get("code_map", {}).items():
                        translated = translated.replace(placeholder, code_html)
                    inline_tags = block.find_all(['a', 'span', 'b', 'i', 'strong', 'em', 'u'])
                    if inline_tags:
                        text_nodes = [n for n in block.find_all(string=True) if n.strip()]
                        if text_nodes:
                            text_nodes[0].replace_with(translated)
                            for n in text_nodes[1:]:
                                n.extract()
                        else:
                            block.clear()
                    else:
                        block.clear()
                        replacement = BeautifulSoup(translated, 'html.parser')
                        contents = list(replacement.body.children) if replacement.body else [replacement]
                        for child in contents:
                            block.append(child)
            block_idx += 1
        result = str(soup).replace('\r\n', '\n').replace('\r', '\n')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"  {rel_path}: OK")
    ncx_segs = [e for e in entries if e["file"].endswith('.ncx') and e["translated"]]
    if ncx_segs:
        ncx_path = os.path.join(extract_to, ncx_segs[0]["file"])
        if os.path.exists(ncx_path):
            with open(ncx_path, 'r', encoding='utf-8') as f:
                ncx = f.read()
            ncx_map = {e["text"]: e["translated"] for e in ncx_segs if e["translated"]}
            ncx_fixed = re.sub(r'<text>(.*?)</text>',
                lambda m: m.group(0).replace(m.group(1), ncx_map.get(m.group(1), m.group(1))),
                ncx)
            with open(ncx_path, 'w', encoding='utf-8') as f:
                f.write(ncx_fixed)
            print(f"  {ncx_segs[0]['file']}: NCX patched")
    output_epub = output_epub or str(Path(epub_path).with_stem(Path(epub_path).stem + "_translated"))
    print(f"Packing -> {output_epub}")
    with zipfile.ZipFile(output_epub, 'w', zipfile.ZIP_DEFLATED) as z:
        mt = os.path.join(extract_to, 'mimetype')
        if os.path.exists(mt):
            z.write(mt, 'mimetype', compress_type=zipfile.ZIP_STORED)
        for root, _, files in os.walk(extract_to):
            for f in files:
                fp = os.path.join(root, f)
                arc = os.path.relpath(fp, extract_to)
                if arc == 'mimetype':
                    continue
                z.write(fp, arc)
    print(f"Done: {output_epub}")

def show_info(translation_json):
    with open(translation_json, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    total = len(entries)
    done = sum(1 for e in entries if e["translated"] is not None)
    total_chars = sum(len(e["text"]) for e in entries)
    done_chars = sum(len(e["translated"]) for e in entries if e["translated"] is not None)
    file_count = len(set(e["file"] for e in entries))
    print(f"Segments: {total}")
    print(f"Translated: {done} ({done*100//total}%)")
    print(f"Source chars: {total_chars}")
    print(f"Translation chars: {done_chars}")
    print(f"Files: {file_count}")
    if done_chars > 0 and total_chars > 0:
        print(f"Expansion ratio: {done_chars/total_chars:.2f}x")
    print(f"\nPer file ({file_count} files):")
    by_file = {}
    for e in entries:
        by_file.setdefault(e["file"], {"total": 0, "done": 0})
        by_file[e["file"]]["total"] += 1
        if e["translated"]:
            by_file[e["file"]]["done"] += 1
    for f, s in sorted(by_file.items()):
        bar_len = 20
        filled = s["done"] * bar_len // s["total"] if s["total"] else 0
        bar = "#" * filled + "-" * (bar_len - filled)
        pct = s["done"] * 100 // s["total"] if s["total"] else 0
        print(f"  {f}: [{bar}] {s['done']}/{s['total']} ({pct}%)")

def verify(translation_json):
    with open(translation_json, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    issues = []
    total = len(entries)
    done = sum(1 for e in entries if e["translated"] is not None)
    if done < total:
        issues.append(f"Incomplete: {total - done} of {total} segments untranslated")
    by_file = {}
    for e in entries:
        by_file[e["file"]] = by_file.get(e["file"], 0) + 1
    large = {f: c for f, c in by_file.items() if c > 300}
    if large:
        for f, c in large.items():
            issues.append(f"Large file: {f} has {c} segments")
    if not issues:
        print(f"Verified: {done}/{total} segments, no issues found.")
    else:
        print(f"Found {len(issues)} issue(s):")
        for i in issues:
            print(f"  - {i}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="EPUB translation toolkit")
    sub = parser.add_subparsers(dest="mode", required=True)
    p_export = sub.add_parser("export", help="Extract translatable text from EPUB")
    p_export.add_argument("epub", help="Path to EPUB file")
    p_export.add_argument("-o", "--output", default="translations.json")
    p_build = sub.add_parser("build", help="Inject translations and rebuild EPUB")
    p_build.add_argument("epub", help="Original EPUB file")
    p_build.add_argument("translations", help="Translated JSON")
    p_build.add_argument("-o", "--output", help="Output EPUB path")
    p_info = sub.add_parser("info", help="Show translation progress")
    p_info.add_argument("translations", help="JSON file path")
    p_verify = sub.add_parser("verify", help="Check for issues before build")
    p_verify.add_argument("translations", help="JSON file path")
    args = parser.parse_args()
    if args.mode == "export":
        extract_and_export(args.epub, args.output)
    elif args.mode == "build":
        inject_and_build(args.epub, args.translations, args.output)
    elif args.mode == "info":
        show_info(args.translations)
    elif args.mode == "verify":
        verify(args.translations)

if __name__ == "__main__":
    main()
