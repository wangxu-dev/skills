---
name: epub-translate
description: AI-assisted EPUB book translation. Extracts text while preserving code blocks, supports progressive batch translation via JSON workflow, and rebuilds translated EPUBs. Language-agnostic — works with any source/target language pair. Use when translating EPUB books or batch-processing book translations with AI assistance.
license: MIT
---

# EPUB Translate

Translate EPUB books with AI assistance. Three phases: extract → translate → build.

## When to Use

- User wants to translate an EPUB book from one language to another
- Extract translatable content from an EPUB for batch processing
- Build a translated EPUB from completed translations
- Check translation progress or verify translation completeness

## Project Setup

```bash
mkdir "Book-Name-Translation"
cd "Book-Name-Translation"
cp /path/to/source.epub ./source.epub
```

Always copy the source file. Never modify the user's original.

## Phase 1: Export

```bash
python scripts/epub_translator.py export ./source.epub -o translations.json
```

What happens:
- Extracts all translatable text from EPUB (XHTML/HTML files)
- Groups text by leaf block elements (`<p>`, `<h1>`, `<li>`, etc.)
- Container blocks (`<div>`, `<section>` with child blocks) are skipped — their children are extracted individually
- `<code>` blocks become `⌜CODE_N⌝` placeholders
- NCX navigation files (`.ncx`) are also parsed for TOC entries
- Outputs a flat JSON array

```json
{"idx": 0, "file": "ch1.xhtml", "text": "Original text", "code_map": {}, "translated": null}
```

After export:
```bash
python scripts/epub_translator.py info translations.json
```

## Phase 2: Translate

Work in batches of 100-200 segments. Process in order.

```bash
python scripts/batch_translate.py extract translations.json 0 100
# Translate batch_0_100.txt → batch_0_100_translated.json
python scripts/batch_translate.py inject translations.json batch_0_100_translated.json
python scripts/epub_translator.py info translations.json
python scripts/batch_translate.py extract translations.json 100 200
```

Critical rules:
- Never translate `⌜CODE_N⌝` placeholders
- Keep technical terms (API names, class names) in original form
- Never reorder or delete segments

## Phase 3: Build

```bash
python scripts/epub_translator.py build ./source.epub translations.json -o "Book-Name-zh.epub"
```

Build process:
1. Reads translations JSON
2. Re-extracts from original EPUB (deletes meta.json cache if BLOCK_TAGS changed)
3. Matches segments to blocks by `block_idx` — export and build must use the same BLOCK_TAGS
4. Restores `⌜CODE_N⌝` → original `<code>` HTML
5. Preserves inline elements (`<a>`, `<span>`, `<b>`, etc.) — only replaces text nodes inside them
6. Skips container blocks (blocks with child blocks) — children are injected individually
7. Processes NCX files — maps `<text>` entries to translations
8. Normalizes line endings to Unix-style
9. Repacks as EPUB

After build, update language metadata:
```bash
# OPF: <dc:language>en</dc:language> → <dc:language>zh</dc:language>
# HTML: lang="en" xml:lang="en" → lang="zh" xml:lang="zh"
```

Then verify the output opens correctly in an EPUB reader.

## Quality Gates

1. **After export**: `info` — check segment count and character volume
2. **After each batch**: `info` — count should increase by batch size
3. **Before build**: `verify` — checks completion, large files, common issues
4. **After build**: Open in reader — verify TOC navigation, code blocks, images, pagination

## Critical Lessons Learned

### 1. Container vs Leaf Blocks
Container blocks (`<div>`, `<section>`) contain other blocks. Never extract or inject into them — their children (`<p>`, `<h1>`, `<li>`) are the actual translation units. Injecting into a container clears all children.

### 2. Inline Tag Preservation
Blocks containing `<a>`, `<span>`, `<strong>`, `<em>` etc. must be handled by replacing only their text nodes, not by clearing and replacing the entire block. Otherwise links (TOC navigation, cross-references) are destroyed.

### 3. BLOCK_TAGS Consistency
Export and build use the same BLOCK_TAGS set. If you change BLOCK_TAGS, delete `translations.json.meta.json` to force re-extraction from the original source.

### 4. NCX Navigation Files
EPUB 2 uses `toc.ncx` for navigation. These files contain `<text>Chapter Title</text>` elements that must be translated separately. The export phase catches them, but the segments must be translated (they're typically the same as the HTML TOC entries).

### 5. Language Metadata
After translating, update the OPF metadata and HTML `lang` attributes from the source language to the target language. Readers (especially Apple Books) use this for typographic rules — CJK text with `lang=en` causes pagination crashes.

### 6. Line Endings
BeautifulSoup serialization produces `\r\n` on Windows. The build phase normalizes to `\n` for cross-platform EPUB compatibility.

## Known Issues

| Issue | Cause | Mitigation |
|-------|-------|-----------|
| Duplicate segments | TOC and body share text | Harmless — both get translated |
| Segments mismatch after rebuild | BLOCK_TAGS changed | Delete meta.json to force re-extract |
| Placeholder appears in output | `⌜CODE_N⌝` not translated | Never translate placeholders — keep verbatim |
| NCX still English | NCX not processed by earlier builds | Rebuild with 0.0.2+ which handles .ncx files |
| Apple Books crash/flash | `lang=en` with CJK content | Update OPF language to target language |
| Terminal can't print Chinese | Windows GBK encoding | Always write output to files, not print |

## Troubleshooting

**"Content is empty after build"** — Likely caused by container blocks. Add `has_block_children` check to skip elements whose children are also in BLOCK_TAGS.

**"TOC links don't work"** — `<a>` tags were cleared during injection. Switch to text-node-only replacement for blocks containing inline elements.

**"Only first page shows"** — Check language metadata. Set `dc:language` and HTML `lang` to match the translation target language.

**"Previous corruption won't go away"** — Delete `translations.json.meta.json` to force a fresh extraction from the original source, then rebuild.
