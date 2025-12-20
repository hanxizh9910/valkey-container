import json
import sys
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

# Repository paths for different registries
DOCKERHUB_REPO_PATH = "valkey/valkey"
DOCKERHUB_IMAGE = "docker.io/valkey/valkey"

ECR_REPO_PATH = "public.ecr.aws/valkey/valkey"
ECR_IMAGE = "public.ecr.aws/valkey/valkey"

def clean_tag(tag: str) -> str:
    if ":" in tag:
        return tag.split(":", 1)[1]
    return tag

def format_tag_line(entry: dict) -> str:
    try:
        meta_entries = entry.get("meta", {}).get("entries", [])
        if not meta_entries:
            raise KeyError("Missing or empty 'entries' list in 'meta'.")
        
        first_entry = meta_entries[0]
        raw_tags = first_entry.get("tags", [])
        if not raw_tags:
            raise KeyError("Missing or empty 'tags' list in entry.")
        
        directory = first_entry.get("directory", None)
        if not directory:
            raise KeyError("Missing 'directory' field in entry.")

        formatted_tags = [f'`{clean_tag(tag)}`' for tag in raw_tags]
        tags = ", ".join(formatted_tags)

        return f"- [{tags}](https://github.com/valkey-io/valkey-container/blob/master/{directory}/Dockerfile)"
    
    except KeyError as e:
        logging.error(f"JSON structure error: {e}")
        raise
    
    except Exception as e:
        logging.error(f"Unexpected error in format_tag_line: {e}")
        raise

def process_template(template_content: str, data: dict, container_repo_path: str, container_image: str) -> str:
    """Process template and return content with placeholders filled."""
    
    official_releases = []
    release_candidates = []
    latest_unstable = []

    for entry in data["matrix"]["include"]:
        line = format_tag_line(entry)
        if "rc" in entry["name"]:
            release_candidates.append(line)
        elif "unstable" in entry["name"]:
            latest_unstable.append(line)
        else:
            official_releases.append(line)

    official_releases_section = "\n".join(official_releases)
    rc_section = "" if not release_candidates else f"\n## Release candidates\n{chr(10).join(release_candidates)}"
    unstable_section = "" if not latest_unstable else f"\n## Latest unstable\n{chr(10).join(latest_unstable)}"

    content = template_content.format(
        update_date=datetime.now().strftime("%Y-%m-%d"),
        official_releases=official_releases_section,
        release_candidates_section=rc_section,
        unstable_section=unstable_section,
        container_repo_path=container_repo_path,
        container_image=container_image
    )

    return content

def parse_ecr_content(md: str) -> tuple:
    """Parse markdown content and return (about_text, usage_text) for ECR."""
    
    # Normalize underlined headings
    md = re.sub(
        r'(?m)^[ \t]*(.+?)\s*\r?\n[ \t]*-{3,}[ \t]*\r?\n',
        r'## \1\n\n',
        md
    )

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

        if "## Latest unstable" in content:
            sub_parts = content.split("## Latest unstable", 1)
            main_content = sub_parts[0].strip()
            unstable_content = sub_parts[1].strip()
            parsed[title] = main_content
            parsed["Latest unstable"] = unstable_content
            continue

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
        heading_prefix = "##" if title == "Latest unstable" else "#"

        if title in usage_sections:
            usage_text += f"{heading_prefix} {title}\n{content}\n\n"
        else:
            about_text += f"{heading_prefix} {title}\n{content}\n\n"

    return about_text.strip(), usage_text.strip()

def update_docker_description(json_file: str, template_file: str) -> None:
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        with open(template_file, 'r') as f:
            template = f.read()

        # Generate Docker Hub description
        dockerhub_content = process_template(template, data, DOCKERHUB_REPO_PATH, DOCKERHUB_IMAGE)
        with open("dockerhub-description.md", 'w') as f:
            f.write(dockerhub_content)
        print("Generated dockerhub-description.md")

        # Generate ECR full description
        ecr_content = process_template(template, data, ECR_REPO_PATH, ECR_IMAGE)
        
        # Parse ECR content into about and usage sections
        about_text, usage_text = parse_ecr_content(ecr_content)
        
        # Write ECR about file
        with open("ecr-about.md", 'w') as f:
            f.write(about_text)
        print("Generated ecr-about.md")
        
        # Write ECR usage file
        with open("ecr-usage.md", 'w') as f:
            f.write(usage_text)
        print("Generated ecr-usage.md")

    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error(f"Failed to parse JSON file '{json_file}'. Please check its syntax.")
        sys.exit(1)
    except KeyError as e:
        logging.error(f"Invalid JSON structure: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error processing data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        logging.error("Invalid number of arguments.")
        logging.error("Usage: python generate-repo-description.py <json_file> <template_file>")
        sys.exit(1)

    try:
        update_docker_description(sys.argv[1], sys.argv[2])
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)