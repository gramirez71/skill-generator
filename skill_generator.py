#!/usr/bin/env python3
"""
Interactive SKILL.md generator for Copilot skills (opencode-compatible).
Saves a SKILL.md file built from user answers.
"""
import json
import textwrap

def prompt(prompt_text, default=None):
    if default:
        resp = input(f"{prompt_text} [{default}]: ")
        return resp.strip() or default
    return input(f"{prompt_text}: ").strip()

def prompt_multiline(prompt_text):
    print(f"{prompt_text} (end with a line containing only END)")
    lines = []
    while True:
        line = input()
        if line.strip() == 'END':
            break
        lines.append(line)
    return '\n'.join(lines).strip()

def prompt_list_of_fields(kind_name):
    items = []
    count = prompt(f"How many {kind_name}? (0 for none)", "0")
    try:
        n = int(count)
    except ValueError:
        n = 0
    for i in range(max(0, n)):
        print(f"\n{kind_name[:-1].capitalize()} #{i+1}")
        name = prompt("  name")
        typ = prompt("  type", "string")
        desc = prompt_multiline("  description")
        items.append({"name": name, "type": typ, "description": desc})
    return items

def render_frontmatter(meta):
    # Render YAML-like frontmatter
    lines = ["---"]
    for k, v in meta.items():
        if v is None or v == "":
            continue
        if isinstance(v, list):
            if not v:
                continue
            lines.append(f"{k}:")
            for item in v:
                if isinstance(item, dict):
                    lines.append("  -")
                    for kk, vv in item.items():
                        safe = vv.replace('\n', '\n    ')
                        lines.append(f"    {kk}: |\n      {textwrap.indent(safe, '      ').strip()}")
                else:
                    lines.append(f"  - {item}")
        elif isinstance(v, bool):
            lines.append(f"{k}: {str(v).lower()}")
        else:
            # simple scalar
            lines.append(f"{k}: {v}")
    lines.append("---\n")
    return '\n'.join(lines)

def main():
    print("Copilot SKILL.md generator (opencode-friendly)\n")
    skill_id = prompt("Skill id (machine-friendly, e.g. my-skill)")
    title = prompt("Title")
    version = prompt("Version", "0.1.0")
    author = prompt("Author (name <email> optional)")
    license = prompt("License (SPDX id)", "MIT")
    repo = prompt("Repository URL (optional)")
    tags = prompt("Comma-separated tags", "copilot,skill").split(',')
    tags = [t.strip() for t in tags if t.strip()]
    opencode_resp = prompt("Mark as opencode-compatible? (y/n)", "y")
    opencode = opencode_resp.lower().startswith('y')

    print("\nEnter a short description:")
    short_desc = prompt_multiline("Short description")
    print("\nEnter a longer description (markdown) or END on its own line to finish):")
    long_desc = prompt_multiline("Long description")

    inputs = prompt_list_of_fields("inputs")
    outputs = prompt_list_of_fields("outputs")

    print("\nDefine triggers/commands (one per line, END to finish):")
    triggers_text = prompt_multiline("Triggers/commands")
    triggers = [t.strip() for t in triggers_text.splitlines() if t.strip()]

    print("\nProvide examples or usage notes (END to finish):")
    examples = prompt_multiline("Examples")

    target_path = prompt("Output path for SKILL.md", "./SKILL.md")

    metadata = {
        "id": skill_id,
        "title": title,
        "version": version,
        "author": author,
        "license": license,
        "repository": repo,
        "tags": tags,
        "opencode": opencode,
        "inputs": inputs,
        "outputs": outputs,
        "triggers": triggers,
    }

    fm = render_frontmatter(metadata)

    body_parts = []
    if short_desc:
        body_parts.append(short_desc)
    if long_desc:
        body_parts.append(long_desc)
    if inputs:
        body_parts.append("## Inputs\n" + '\n'.join([f"- **{i['name']}** ({i['type']}): {i['description']}" for i in inputs]))
    if outputs:
        body_parts.append("## Outputs\n" + '\n'.join([f"- **{o['name']}** ({o['type']}): {o['description']}" for o in outputs]))
    if triggers:
        body_parts.append("## Triggers/Commands\n" + '\n'.join([f"- {t}" for t in triggers]))
    if examples:
        body_parts.append("## Examples\n" + examples)

    body = '\n\n'.join(body_parts).strip()
    content = fm + body + "\n"

    print('\n---\nPreview of SKILL.md:\n')
    print(content)

    confirm = prompt("Write SKILL.md to: {}? (y/n)".format(target_path), "y")
    if confirm.lower().startswith('y'):
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Wrote SKILL.md to {target_path}")
    else:
        print("Aborted. No file written.")

if __name__ == '__main__':
    main()
