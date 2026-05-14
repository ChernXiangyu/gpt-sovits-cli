import re
import pathlib

import sys
src_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(r"D:\gpt-sovits-cli\inputs\attention_essay.txt")
out_path = src_path.with_name(src_path.stem + "_clean" + src_path.suffix)

t = src_path.read_text(encoding="utf-8")
orig = len(t)

# Markdown emphasis: **bold**, *italic*
t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
t = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"\1", t)

# Headings
t = re.sub(r"^#+\s+", "", t, flags=re.M)

# Horizontal rules
t = re.sub(r"^---+\s*$", "", t, flags=re.M)

# Inline math/code: $...$
t = re.sub(r"\$([^$\n]+)\$", r"\1", t)
t = t.replace("$", "")

# Bullets
t = re.sub(r"^[-*]\s+", "", t, flags=re.M)

# Blockquote markers
t = re.sub(r"^>\s+", "", t, flags=re.M)

# Collapse repeated blank lines
t = re.sub(r"\n{3,}", "\n\n", t).strip() + "\n"

out_path.write_text(t, encoding="utf-8")
print("Original:", orig, "chars  Cleaned:", len(t), "chars")
print("--- preview (first 400) ---")
print(t[:400])
