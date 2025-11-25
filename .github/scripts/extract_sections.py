import sys
import json
import re

# Read entire markdown file
with open(sys.argv[1], "r") as f:
    md = f.read()

# Split by top-level headings (# ...)
sections = re.split(r"(?m)^# ", md)
parsed = {}

# The first chunk before the first "# " is useless, skip it
for sec in sections[1:]:
    # Extract title (text until newline)
    title, _, content = sec.partition("\n")
    title = title.strip()
    parsed[title] = content.strip()

# Sections we want in usage
usage_sections = [
    "How to use this image",
    "Image Variants"
]

usage_text = ""
about_text = ""

for title, content in parsed.items():
    if title in usage_sections:
        usage_text += f"# {title}\n{content}\n\n"
    else:
        about_text += f"# {title}\n{content}\n\n"

# Output JSON for GitHub Actions
print(json.dumps({
    "usage": usage_text.strip(),
    "about": about_text.strip()
}))
