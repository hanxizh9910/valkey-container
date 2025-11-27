import sys
import json
import re
import os

# Read entire markdown file
with open(sys.argv[1], "r") as f:
    md = f.read()

# Split by top-level headings (# ...)
sections = re.split(r"(?m)^# ", md)

# The first chunk (before first "# ") contains the auto-generated notice
preamble = sections[0].strip() if sections[0].strip() else ""

parsed = {}

# Process the actual sections (skip the preamble at index 0)
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

# Start about_text with the preamble (auto-generated notice)
if preamble:
    preamble = re.sub(r'^##\s*', '', preamble, flags=re.MULTILINE)
    about_text = f"{preamble}\n\n"

# Add sections to appropriate text blocks
for title, content in parsed.items():
    if title in usage_sections:
        usage_text += f"# {title}\n{content}\n\n"
    else:
        about_text += f"# {title}\n{content}\n\n"

# Write to GitHub Actions environment file
with open(os.environ['GITHUB_ENV'], 'a') as f:
    f.write(f"ABOUT_JSON={json.dumps(about_text.strip())}\n")
    f.write(f"USAGE_JSON={json.dumps(usage_text.strip())}\n")

# Optional: Print confirmation
print("Successfully parsed markdown and wrote to environment variables")
