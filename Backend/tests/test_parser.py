import pytest
from fastapi.testclient import TestClient

from app.services.parser import (
    parse_package_json_content,
    parse_requirements_txt_content,
    clean_version,
    compare_versions,
    is_valid_version,
)


class TestPackageJsonParsing:
    """Test package.json parsing functionality."""
    
    def test_parse_valid_package_json(self, sample_package_json):
        """Test parsing a valid package.json."""
        import json
        content = json.dumps(sample_package_json)
        
        dependencies = parse_package_json_content(content)
        
        assert len(dependencies) == 5
        
        # Check dependencies
        prod_deps = [d for d in dependencies if not d.is_dev]
        dev_deps = [d for d in dependencies if d.is_dev]
        
        assert len(prod_deps) == 3
        assert len(dev_deps) == 2
        
        # Check specific dependency
        express_dep = next((d for d in dependencies if d.name == "express"), None)
        assert express_dep is not None
        assert express_dep.declared_constraint == "4.17.1"
        assert express_dep.resolved_version == "4.17.1"
        assert express_dep.ecosystem == "npm"
        assert not express_dep.is_dev
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        with pytest.raises(ValueError):
            parse_package_json_content("{invalid json}")
    
    def test_parse_empty_dependencies(self):
        """Test parsing package.json with no dependencies."""
        content = '{"name": "test", "version": "1.0.0"}'
        dependencies = parse_package_json_content(content)
        assert len(dependencies) == 0
    
    def test_version_cleaning(self):
        """Test version constraint cleaning."""
        assert clean_version("^4.17.1") == "4.17.1"
        assert clean_version("~2.3.0") == "2.3.0"
        assert clean_version(">=1.2.3") == "1.2.3"
        assert clean_version("1.2") == "1.2.0"
        assert clean_version("*") is None
        assert clean_version("latest") is None
        assert clean_version("git+https://github.com/user/repo.git") is None


class TestRequirementsTxtParsing:
    """Test requirements.txt parsing functionality."""
    
    def test_parse_valid_requirements(self, sample_requirements_txt):
        """Test parsing a valid requirements.txt."""
        dependencies = parse_requirements_txt_content(sample_requirements_txt)
        
        assert len(dependencies) == 5
        
        # Check specific dependency
        requests_dep = next((d for d in dependencies if d.name == "requests"), None)
        assert requests_dep is not None
        assert requests_dep.declared_constraint == "==2.28.0"
        assert requests_dep.ecosystem == "pypi"
        assert not requests_dep.is_dev
        
        # Check version constraint parsing
        flask_dep = next((d for d in dependencies if d.name == "flask"), None)
        assert flask_dep is not None
        assert flask_dep.declared_constraint == ">=2.0.0"
    
    def test_parse_empty_requirements(self):
        """Test parsing empty requirements.txt."""
        dependencies = parse_requirements_txt_content("")
        assert len(dependencies) == 0
    
    def test_parse_with_comments(self):
        """Test parsing requirements.txt with comments."""
        content = """# This is a comment
requests==2.28.0
# Another comment
flask>=2.0.0"""
        
        dependencies = parse_requirements_txt_content(content)
        assert len(dependencies) == 2


class TestVersionComparison:
    """Test version comparison functionality."""
    
    def test_compare_versions(self):
        """Test version comparison."""
        assert compare_versions("1.0.0", "2.0.0") == -1
        assert compare_versions("2.0.0", "1.0.0") == 1
        assert compare_versions("1.0.0", "1.0.0") == 0
        
        assert compare_versions("1.2.3", "1.2.4") == -1
        assert compare_versions("1.2.4", "1.2.3") == 1
    
    def test_is_valid_version(self):
        """Test version validity checking."""
        assert is_valid_version("1.0.0")
        assert is_valid_version("1.2.3-alpha.1")
        assert is_valid_version("2.0.0-rc.1")
        assert not is_valid_version("invalid-version")