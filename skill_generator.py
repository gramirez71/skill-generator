#!/usr/bin/env python3
"""
Interactive SKILL.md generator for Copilot skills (opencode-compatible).
Saves a SKILL.md file built from user answers.
"""
import argparse
import os
import sys
import textwrap

VERSION = "0.1.0"

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

def _yaml_escape_multiline(text):
    """Return YAML-safe representation of a potentially multiline string
    using a literal block scalar (|). Handles special characters and
    trailing whitespace by folding into a quoted scalar when unsafe."""
    if not text:
        return '""'
    has_special = ':' in text or '#' in text or text.startswith(('{', '['))
    needs_multiline = '\n' in text
    if needs_multiline:
        # Use a |-style literal block for multiline content.
        # The block header goes on the same indent as the key value.
        # We indent all content lines by the caller's base indent.
        return "|\n" + textwrap.indent(text, '        ')
    elif has_special:
        safe = text.replace('"', '\\"')
        return f'"{safe}"'
    else:
        safe = text.replace('"', '\\"')
        return f'"{safe}"'

def render_frontmatter(meta):
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
                        safe = _yaml_escape_multiline(vv)
                        if '\n' in safe:
                            lines.append(f"    {kk}: {safe}")
                        else:
                            lines.append(f"    {kk}: {safe}")
                else:
                    lines.append(f"  - {item}")
        elif isinstance(v, bool):
            lines.append(f"{k}: {str(v).lower()}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---\n")
    return '\n'.join(lines)

def run_interactive(args):
    print("Copilot SKILL.md generator (opencode-friendly)\n")

    skill_id = ""
    while not skill_id.strip():
        skill_id = prompt("Skill id (machine-friendly, e.g. my-skill)", args.id)

    title = ""
    while not title.strip():
        title = prompt("Title", args.title)

    version = prompt("Version", args.skversion or "0.1.0")
    author = prompt("Author (name <email> optional)", args.author)
    license = prompt("License (SPDX id)", args.license or "MIT")
    repo = prompt("Repository URL (optional)", args.repository)

    tags_val = args.tags or "copilot,skill"
    tags = prompt("Comma-separated tags", tags_val).split(',')
    tags = [t.strip() for t in tags if t.strip()]

    opencode_resp = prompt("Mark as opencode-compatible? (y/n)", "y")
    opencode = opencode_resp.lower().startswith('y')

    print("\nEnter a short description:")
    short_desc = prompt_multiline("Short description")
    print("\nEnter a longer description (markdown, END to finish):")
    long_desc = prompt_multiline("Long description")

    inputs = prompt_list_of_fields("inputs")
    outputs = prompt_list_of_fields("outputs")

    print("\nDefine triggers/commands (one per line, END to finish):")
    triggers_text = prompt_multiline("Triggers/commands")
    triggers = [t.strip() for t in triggers_text.splitlines() if t.strip()]

    print("\nProvide examples or usage notes (END to finish):")
    examples = prompt_multiline("Examples")

    target_path = prompt("Output path for SKILL.md", args.output or "./SKILL.md")

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
        if os.path.exists(target_path):
            overwrite = prompt(
                f"File '{target_path}' already exists. Overwrite? (y/n)",
                "n",
            )
            if not overwrite.lower().startswith('y'):
                print("Aborted. No file written.")
                return
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Wrote SKILL.md to {target_path}")
    else:
        print("Aborted. No file written.")

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Interactive Copilot SKILL.md generator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python skill_generator.py
              python skill_generator.py --id my-skill --title "My Skill" --no-interact
        """),
    )
    parser.add_argument(
        "-v", "--tool-version", action="version", version=f"%(prog)s {VERSION}"
    )
    parser.add_argument("--id", help="Skill id (machine-friendly)")
    parser.add_argument("--title", help="Skill title")
    parser.add_argument(
        "--version", dest="skversion", help="Skill version (default 0.1.0)"
    )
    parser.add_argument("--author", help="Author (name <email>)")
    parser.add_argument("--license", help="License SPDX id (default MIT)")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--repository", help="Repository URL")
    parser.add_argument("--output", help="Path for generated SKILL.md")
    parser.add_argument(
        "--no-interact",
        action="store_true",
        help="Skip interactive prompts and use provided args only",
    )

    return parser.parse_args(argv)

def run(args):
    if not args.no_interact:
        run_interactive(args)
    else:
        if not args.id:
            print("Error: --id is required in non-interactive mode", file=sys.stderr)
            sys.exit(1)
        if not args.title:
            print("Error: --title is required in non-interactive mode", file=sys.stderr)
            sys.exit(1)

        tags = (args.tags or "copilot,skill").split(',')
        tags = [t.strip() for t in tags if t.strip()]
        target_path = args.output or "./SKILL.md"

        metadata = {
            "id": args.id,
            "title": args.title,
            "version": args.skversion or "0.1.0",
            "author": args.author,
            "license": args.license or "MIT",
            "repository": args.repository,
            "tags": tags,
            "opencode": True,
            "inputs": [],
            "outputs": [],
            "triggers": [],
        }

        fm = render_frontmatter(metadata)
        body = f"{args.title} skill."
        content = fm + body + "\n"

        if os.path.exists(target_path):
            print(
                f"Error: '{target_path}' already exists. Use --output to specify "
                "a different path.",
                file=sys.stderr,
            )
            sys.exit(1)

        print(f"Writing SKILL.md to {target_path}")
        print(fm + body + "\n")
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Wrote SKILL.md to {target_path}")

def main():
    args = parse_args(sys.argv[1:])
    run(args)

if __name__ == '__main__':
    main()