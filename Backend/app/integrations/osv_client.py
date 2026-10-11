import asyncio
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.core.exceptions import ExternalAPIException

OSV_API_URL = settings.osv_api_url
SEVERITY_ORDER = ["UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
MAX_CONCURRENT = settings.max_concurrent_requests


class OSVClient:
    """Client for interacting with the OSV (Open Source Vulnerabilities) API."""
    
    def __init__(self):
        self.api_url = OSV_API_URL
        self.timeout = settings.request_timeout
    
    def _extract_severity(self, vuln: Dict[str, Any]) -> str:
        """Extract severity from vulnerability data."""
        # Try database_specific.severity first (GitHub advisories)
        db_specific = vuln.get("database_specific", {})
        severity = str(db_specific.get("severity", "")).upper()
        
        # Normalize MODERATE to MEDIUM
        if severity == "MODERATE":
            severity = "MEDIUM"
        
        # Try severity from other sources
        if severity not in SEVERITY_ORDER:
            # Check for CVSS scores
            severity_info = vuln.get("severity", [])
            if severity_info and isinstance(severity_info, list):
                for sev in severity_info:
                    if isinstance(sev, dict):
                        score_type = sev.get("type", "").upper()
                        if score_type == "CVSS_V3":
                            score = sev.get("score")
                            if score:
                                severity = self._cvss_score_to_severity(score)
                                break
        
        return severity if severity in SEVERITY_ORDER else "UNKNOWN"
    
    def _cvss_score_to_severity(self, cvss_score: float) -> str:
        """Convert CVSS score to severity level."""
        if cvss_score >= 9.0:
            return "CRITICAL"
        elif cvss_score >= 7.0:
            return "HIGH"
        elif cvss_score >= 4.0:
            return "MEDIUM"
        elif cvss_score > 0.0:
            return "LOW"
        else:
            return "UNKNOWN"
    
    def _extract_fixed_versions(self, vuln: Dict[str, Any], package_name: str) -> List[str]:
        """Extract fixed versions from vulnerability data."""
        fixed_versions = set()
        
        for affected in vuln.get("affected", []):
            pkg_info = affected.get("package", {})
            if pkg_info.get("name") != package_name:
                continue
            
            for version_range in affected.get("ranges", []):
                for event in version_range.get("events", []):
                    if "fixed" in event:
                        fixed_versions.add(event["fixed"])
        
        return sorted(fixed_versions)
    
    def _extract_affected_versions(self, vuln: Dict[str, Any], package_name: str) -> List[str]:
        """Extract affected version ranges from vulnerability data."""
        affected_ranges = []
        
        for affected in vuln.get("affected", []):
            pkg_info = affected.get("package", {})
            if pkg_info.get("name") != package_name:
                continue
            
            # Extract specific affected versions
            versions = affected.get("versions", [])
            if versions:
                affected_ranges.extend(versions)
            
            # Extract version ranges
            for version_range in affected.get("ranges", []):
                range_type = version_range.get("type", "SEMVER")
                events = version_range.get("events", [])
                
                # Build range string from events
                range_str = f"{range_type}:"
                for event in events:
                    if "introduced" in event:
                        range_str += f" >={event['introduced']}"
                    elif "fixed" in event:
                        range_str += f" <{event['fixed']}"
                    elif "last_affected" in event:
                        range_str += f" <={event['last_affected']}"
                
                if range_str != f"{range_type}:":
                    affected_ranges.append(range_str)
        
        return affected_ranges
    
    def _parse_vulnerability(self, vuln: Dict[str, Any], package_name: str) -> Dict[str, Any]:
        """Parse vulnerability data into structured format."""
        return {
            "id": vuln.get("id", ""),
            "summary": vuln.get("summary", "No summary available"),
            "description": vuln.get("details", ""),
            "severity": self._extract_severity(vuln),
            "fixed_versions": self._extract_fixed_versions(vuln, package_name),
            "affected_versions": self._extract_affected_versions(vuln, package_name),
            "aliases": vuln.get("aliases", []),
            "references": [ref.get("url", "") for ref in vuln.get("references", [])],
            "published": vuln.get("published"),
            "modified": vuln.get("modified"),
        }
    
    async def check_vulnerability(
        self,
        package_name: str,
        version: str,
        ecosystem: str
    ) -> Dict[str, Any]:
        """
        Check a single package version for vulnerabilities.
        
        Args:
            package_name: Name of the package
            version: Version to check
            ecosystem: Package ecosystem (npm, pypi, etc.)
            
        Returns:
            Dictionary with vulnerability check results
        """
        if not version:
            return {
                "name": package_name,
                "version": None,
                "ecosystem": ecosystem,
                "status": "skipped",
                "vulnerabilities": [],
                "error": "Version could not be resolved"
            }
        
        payload = {
            "version": version,
            "package": {
                "name": package_name,
                "ecosystem": ecosystem
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.api_url, json=payload)
                response.raise_for_status()
                data = response.json()
            
            vulnerabilities = data.get("vulns", [])
            parsed_vulns = [
                self._parse_vulnerability(vuln, package_name)
                for vuln in vulnerabilities
            ]
            
            return {
                "name": package_name,
                "version": version,
                "ecosystem": ecosystem,
                "status": "vulnerable" if parsed_vulns else "safe",
                "vulnerabilities": parsed_vulns,
                "error": None
            }
            
        except httpx.TimeoutException:
            return {
                "name": package_name,
                "version": version,
                "ecosystem": ecosystem,
                "status": "error",
                "vulnerabilities": [],
                "error": f"Timeout checking vulnerabilities for {package_name}@{version}"
            }
        except httpx.HTTPStatusError as e:
            return {
                "name": package_name,
                "version": version,
                "ecosystem": ecosystem,
                "status": "error",
                "vulnerabilities": [],
                "error": f"HTTP error checking vulnerabilities: {e}"
            }
        except Exception as e:
            return {
                "name": package_name,
                "version": version,
                "ecosystem": ecosystem,
                "status": "error",
                "vulnerabilities": [],
                "error": f"Unexpected error checking vulnerabilities: {e}"
            }
    
    async def batch_check_vulnerabilities(
        self,
        dependencies: List[Dict[str, Any]],
        max_concurrent: int = None
    ) -> List[Dict[str, Any]]:
        """
        Check multiple dependencies for vulnerabilities concurrently.
        
        Args:
            dependencies: List of dependency dictionaries with name, version, ecosystem
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of vulnerability check results
        """
        if max_concurrent is None:
            max_concurrent = MAX_CONCURRENT
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def check_single_dependency(dep: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.check_vulnerability(
                    package_name=dep["name"],
                    version=dep.get("version"),
                    ecosystem=dep.get("ecosystem", "npm")
                )
        
        tasks = [check_single_dependency(dep) for dep in dependencies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                dep = dependencies[i]
                final_results.append({
                    "name": dep["name"],
                    "version": dep.get("version"),
                    "ecosystem": dep.get("ecosystem", "npm"),
                    "status": "error",
                    "vulnerabilities": [],
                    "error": f"Exception during vulnerability check: {result}"
                })
            else:
                final_results.append(result)
        
        return final_results


# Global OSV client instance
osv_client = OSVClient()


# Legacy compatibility functions
async def check_all_dependencies(dependencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility."""
    # Convert legacy format to new format
    converted_deps = []
    for dep in dependencies:
        converted_deps.append({
            "name": dep["name"],
            "version": dep.get("version"),
            "ecosystem": "npm"  # Legacy function assumes npm
        })
    
    results = await osv_client.batch_check_vulnerabilities(converted_deps)
    
    # Convert back to legacy format
    legacy_results = []
    for result in results:
        legacy_result = {
            "name": result["name"],
            "version": result["version"],
            "spec": dependencies[len(legacy_results)].get("spec", ""),  # Get original spec
            "dev": dependencies[len(legacy_results)].get("dev", False),  # Get original dev flag
            "status": result["status"],
            "vulnerabilities": []
        }
        
        if result["status"] == "error":
            legacy_result["error"] = result["error"]
        
        # Convert vulnerabilities to legacy format
        for vuln in result["vulnerabilities"]:
            legacy_result["vulnerabilities"].append({
                "id": vuln["id"],
                "summary": vuln["summary"],
                "severity": vuln["severity"],
                "fixed_versions": vuln["fixed_versions"],
                "aliases": vuln["aliases"],
            })
        
        legacy_results.append(legacy_result)
    
    return legacy_results