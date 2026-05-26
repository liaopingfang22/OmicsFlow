import os
import yaml
from pathlib import Path
from typing import Optional


class SkillLoader:
    def __init__(self, skills_dir: str = None):
        if skills_dir is None:
            from config import get_settings
            settings = get_settings()
            skills_dir = str(Path(settings.workflow_dir).parent / "skills")
        self.skills_dir = Path(skills_dir)
        self._registry = None
        self._skills_content = {}

    def load_registry(self) -> dict:
        if self._registry is None:
            registry_file = self.skills_dir / "registry.yaml"
            if registry_file.exists():
                with open(registry_file) as f:
                    self._registry = yaml.safe_load(f)
            else:
                self._registry = {}
        return self._registry

    def load_skill(self, skill_name: str) -> Optional[str]:
        if skill_name in self._skills_content:
            return self._skills_content[skill_name]

        for md_file in self.skills_dir.glob("*.md"):
            if md_file.stem == skill_name:
                with open(md_file) as f:
                    self._skills_content[skill_name] = f.read()
                return self._skills_content[skill_name]
        return None

    def list_skills(self, category: Optional[str] = None) -> list:
        registry = self.load_registry()
        if not registry:
            return []
        
        skills = []
        for name, info in registry.items():
            if category is None or info.get("category") == category:
                skills.append({
                    "name": name,
                    "description": info.get("description", ""),
                    "category": info.get("category", ""),
                    "version": info.get("version", "1.0"),
                })
        return skills

    def get_skill_by_name(self, name: str) -> Optional[dict]:
        content = self.load_skill(name)
        if not content:
            return None

        registry = self.load_registry()
        info = registry.get(name, {})

        return {
            "name": name,
            "content": content,
            "description": info.get("description", ""),
            "category": info.get("category", ""),
            "version": info.get("version", "1.0"),
        }


skill_loader = SkillLoader()
