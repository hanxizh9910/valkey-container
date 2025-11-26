import sys
import json
import re
import os

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

# Write to GitHub Actions environment file instead of stdout
with open(os.environ['GITHUB_ENV'], 'a') as f:
    f.write(f"ABOUT_JSON={json.dumps(about_text.strip())}\n")
    f.write(f"USAGE_JSON={json.dumps(usage_text.strip())}\n")

# Optional: Print confirmation (this won't interfere with the environment)
print("Successfully parsed markdown and wrote to environment variables")
