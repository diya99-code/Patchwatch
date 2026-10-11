import json
import re
from typing import List, Dict, Any, Optional
from packaging import version

DEP_SECTIONS = {"dependencies": False, "devDependencies": True}  # section -> is_dev
_VERSION_RE = re.compile(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?(-[0-9A-Za-z.\-]+)?")


class ParsedDependency:
    """Represents a parsed dependency from a manifest file."""
    
    def __init__(
        self,
        name: str,
        declared_constraint: str,
        resolved_version: Optional[str] = None,
        is_dev: bool = False,
        ecosystem: str = "npm"
    ):
        self.name = name
        self.declared_constraint = declared_constraint
        self.resolved_version = resolved_version or self._resolve_version(declared_constraint)
        self.is_dev = is_dev
        self.ecosystem = ecosystem
    
    def _resolve_version(self, constraint: str) -> Optional[str]:
        """Extract a concrete version from a version constraint."""
        return clean_version(constraint)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "declared_constraint": self.declared_constraint,
            "resolved_version": self.resolved_version,
            "is_dev": self.is_dev,
            "ecosystem": self.ecosystem
        }


def clean_version(spec: str) -> Optional[str]:
    """
    Turn an npm version spec into one concrete version OSV can look up.
    '^4.17.15' -> '4.17.15', '~1.2' -> '1.2.0', '*' / 'latest' / git urls -> None.
    Note: for ranges this is the *minimum* version the range allows, which is
    a reasonable approximation without a lockfile.
    """
    if not isinstance(spec, str):
        return None
    if spec.startswith(("git", "http", "file:", "link:", "workspace:")):
        return None
    m = _VERSION_RE.search(spec)
    if not m:
        return None
    major, minor, patch, pre = m.groups()
    return f"{major}.{minor or 0}.{patch or 0}{pre or ''}"


def is_valid_version(version_str: str) -> bool:
    """Check if a version string is valid."""
    try:
        version.parse(version_str)
        return True
    except version.InvalidVersion:
        return False


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two version strings.
    Returns: -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
    """
    try:
        ver1 = version.parse(v1)
        ver2 = version.parse(v2)
        
        if ver1 < ver2:
            return -1
        elif ver1 > ver2:
            return 1
        else:
            return 0
    except version.InvalidVersion:
        # Fallback to string comparison for invalid versions
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0


def parse_package_json_content(text: str) -> List[ParsedDependency]:
    """Parse package.json text. Raises json.JSONDecodeError on bad JSON."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    
    if not isinstance(data, dict):
        raise ValueError("package.json must be an object")

    dependencies = []
    for section, is_dev in DEP_SECTIONS.items():
        section_deps = data.get(section, {})
        if not isinstance(section_deps, dict):
            continue
            
        for name, spec in section_deps.items():
            if not isinstance(name, str) or not isinstance(spec, str):
                continue
                
            dep = ParsedDependency(
                name=name,
                declared_constraint=spec,
                is_dev=is_dev,
                ecosystem="npm"
            )
            dependencies.append(dep)
    
    return dependencies


def parse_package_json(path: str) -> List[ParsedDependency]:
    """Parse a package.json file on disk. Raises FileNotFoundError if missing."""
    with open(path, "r", encoding="utf-8") as f:
        return parse_package_json_content(f.read())


def parse_requirements_txt_content(text: str) -> List[ParsedDependency]:
    """Parse requirements.txt content."""
    dependencies = []
    
    for line in text.split('\n'):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Skip editable installs and git URLs for now
        if line.startswith('-e') or line.startswith('git+'):
            continue
        
        # Simple parsing - split on common operators
        name = line
        constraint = line
        
        # Extract package name and version constraint
        for op in ['>=', '<=', '==', '!=', '>', '<', '~=']:
            if op in line:
                name, version_part = line.split(op, 1)
                name = name.strip()
                constraint = f"{op}{version_part.strip()}"
                break
        else:
            # No version specified
            name = line.strip()
            constraint = "*"
        
        # Remove any extras (package[extra])
        if '[' in name:
            name = name.split('[')[0]
        
        if name:
            dep = ParsedDependency(
                name=name,
                declared_constraint=constraint,
                is_dev=False,
                ecosystem="pypi"
            )
            dependencies.append(dep)
    
    return dependencies


def parse_requirements_txt(path: str) -> List[ParsedDependency]:
    """Parse a requirements.txt file on disk."""
    with open(path, "r", encoding="utf-8") as f:
        return parse_requirements_txt_content(f.read())


# Legacy compatibility functions
def parse_package_json_content_legacy(text: str) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility."""
    dependencies = parse_package_json_content(text)
    return [
        {
            "name": dep.name,
            "spec": dep.declared_constraint,
            "version": dep.resolved_version,
            "dev": dep.is_dev,
        }
        for dep in dependencies
    ]


def parse_package_json_legacy(path: str) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility."""
    dependencies = parse_package_json(path)
    return [
        {
            "name": dep.name,
            "spec": dep.declared_constraint,
            "version": dep.resolved_version,
            "dev": dep.is_dev,
        }
        for dep in dependencies
    ]
