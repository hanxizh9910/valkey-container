import json
import sys
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

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

def extract_section(template: str, start_marker: str, end_marker: str) -> str:
    """Extract content between markers."""
    pattern = f"{start_marker}(.*?){end_marker}"
    match = re.search(pattern, template, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def process_template(template_content: str, data: dict) -> tuple:
    """Process template and return (dockerhub_content, ecr_content)."""
    
    # Categorize entries
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

    # Extract sections
    dockerhub_template = extract_section(template_content, "<!-- DOCKERHUB_START -->", "<!-- DOCKERHUB_END -->")
    ecr_template = extract_section(template_content, "<!-- ECR_START -->", "<!-- ECR_END -->")

    # Fill placeholders for each section
    dockerhub_content = dockerhub_template.format(
        update_date=datetime.now().strftime("%Y-%m-%d"),
        official_releases=official_releases_section,
        release_candidates_section=rc_section,
        unstable_section=unstable_section
    )

    ecr_content = ecr_template.format(
        update_date=datetime.now().strftime("%Y-%m-%d"),
        official_releases=official_releases_section,
        release_candidates_section=rc_section,
        unstable_section=unstable_section
    )

    return dockerhub_content, ecr_content

def update_docker_description(json_file: str, template_file: str) -> None:
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        with open(template_file, 'r') as f:
            template = f.read()

        dockerhub_content, ecr_content = process_template(template, data)

        # Write Docker Hub description
        with open("dockerhub-description.md", 'w') as f:
            f.write(dockerhub_content)
        print("Generated dockerhub-description.md")

        # Write ECR description
        with open("ecr-description.md", 'w') as f:
            f.write(ecr_content)
        print("Generated ecr-description.md")

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
        logging.error("Usage: python automate_docker_description.py <json_file> <template_file>")
        sys.exit(1)

    try:
        update_docker_description(sys.argv[1], sys.argv[2])
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)