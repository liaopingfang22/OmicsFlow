#!/usr/bin/env python3
"""Sync bioSkills from GPTomics/bioSkills into OmicsFlow skills directory."""
import os, re, yaml
from pathlib import Path

SRC = Path("/public/xalab/liaopingfang/software/bioSkills")
DST = Path("/public/xalab/liaopingfang/pipeline_test/OmicsFlow/skills")
SKIP = {".git", "resources", "bioskills-installer", "__pycache__"}

def extract_fm(content):
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if m:
        try: return yaml.safe_load(m.group(1)) or {}
        except: pass
    return {}

def main():
    DST.mkdir(parents=True, exist_ok=True)
    registry = {}
    count = 0
    for cat in sorted(SRC.iterdir()):
        if not cat.is_dir() or cat.name in SKIP: continue
        for skill in sorted(cat.iterdir()):
            sf = skill / "SKILL.md"
            if not sf.exists(): continue
            content = sf.read_text(encoding='utf-8')
            fm = extract_fm(content)
            name = fm.get('name', skill.name)
            if not name.startswith('bio-'):
                name = f"bio-{cat.name}-{skill.name}"
            out = DST / f"{name}.md"
            out.write_text(content, encoding='utf-8')
            registry[name] = {
                'description': fm.get('description', ''),
                'category': cat.name,
                'subcategory': skill.name,
                'version': fm.get('version', '1.0'),
            }
            count += 1
    with open(DST / "registry.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(registry, f, default_flow_style=False, allow_unicode=True, sort_keys=True)
    print(f"Synced {count} skills from bioSkills into {DST}")
    print(f"Registry: {len(registry)} entries")

if __name__ == "__main__":
    main()
