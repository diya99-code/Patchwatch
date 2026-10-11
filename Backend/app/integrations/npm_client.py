import asyncio
from typing import Optional, Dict, Any, List
import httpx
from packaging import version

from app.core.config import settings
from app.core.exceptions import ExternalAPIException


class NPMClient:
    """Client for interacting with the npm registry."""
    
    def __init__(self):
        self.base_url = settings.npm_registry_url
        self.timeout = settings.request_timeout
    
    async def get_package_metadata(self, package_name: str) -> Optional[Dict[str, Any]]:
        """
        Get package metadata from npm registry.
        
        Args:
            package_name: The name of the package
            
        Returns:
            Package metadata or None if not found
            
        Raises:
            ExternalAPIException: If API request fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/{package_name}")
                
                if response.status_code == 404:
                    return None
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            raise ExternalAPIException(f"Timeout fetching npm package: {package_name}")
        except httpx.HTTPStatusError as e:
            raise ExternalAPIException(f"HTTP error fetching npm package {package_name}: {e}")
        except Exception as e:
            raise ExternalAPIException(f"Unexpected error fetching npm package {package_name}: {e}")
    
    async def get_latest_version(self, package_name: str) -> Optional[str]:
        """
        Get the latest stable version of a package.
        
        Args:
            package_name: The name of the package
            
        Returns:
            Latest version string or None if not found
        """
        try:
            metadata = await self.get_package_metadata(package_name)
            if not metadata:
                return None
            
            # Get the latest tag version
            dist_tags = metadata.get("dist-tags", {})
            latest = dist_tags.get("latest")
            
            if latest and self._is_stable_version(latest):
                return latest
            
            # Fallback: find latest stable version from versions list
            versions = metadata.get("versions", {}).keys()
            stable_versions = [v for v in versions if self._is_stable_version(v)]
            
            if stable_versions:
                # Sort versions and get the latest
                sorted_versions = sorted(stable_versions, key=version.parse, reverse=True)
                return sorted_versions[0]
            
            return latest  # Return even if not stable
            
        except Exception as e:
            # Log error but don't raise - this is non-critical
            return None
    
    def _is_stable_version(self, version_str: str) -> bool:
        """Check if a version is considered stable (no pre-release tags)."""
        try:
            parsed_version = version.parse(version_str)
            return not parsed_version.is_prerelease
        except version.InvalidVersion:
            return False
    
    async def get_package_info(self, package_name: str) -> Dict[str, Any]:
        """
        Get comprehensive package information.
        
        Args:
            package_name: The name of the package
            
        Returns:
            Dictionary with package information
        """
        try:
            metadata = await self.get_package_metadata(package_name)
            if not metadata:
                return {
                    "name": package_name,
                    "found": False,
                    "latest_version": None,
                    "description": None,
                    "homepage": None,
                }
            
            latest_version = await self.get_latest_version(package_name)
            
            return {
                "name": package_name,
                "found": True,
                "latest_version": latest_version,
                "description": metadata.get("description"),
                "homepage": metadata.get("homepage"),
                "repository": metadata.get("repository"),
                "license": metadata.get("license"),
                "author": metadata.get("author"),
                "dist_tags": metadata.get("dist-tags", {}),
                "time": metadata.get("time", {}),
            }
            
        except ExternalAPIException:
            # Re-raise API exceptions
            raise
        except Exception as e:
            raise ExternalAPIException(f"Error getting package info for {package_name}: {e}")
    
    async def batch_get_latest_versions(
        self,
        package_names: List[str],
        max_concurrent: int = None
    ) -> Dict[str, Optional[str]]:
        """
        Get latest versions for multiple packages concurrently.
        
        Args:
            package_names: List of package names
            max_concurrent: Maximum concurrent requests
            
        Returns:
            Dictionary mapping package names to their latest versions
        """
        if max_concurrent is None:
            max_concurrent = settings.max_concurrent_requests
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def get_single_version(package_name: str) -> tuple[str, Optional[str]]:
            async with semaphore:
                latest_version = await self.get_latest_version(package_name)
                return package_name, latest_version
        
        tasks = [get_single_version(name) for name in package_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        version_map = {}
        for result in results:
            if isinstance(result, Exception):
                # Log the error but continue with other packages
                continue
            
            package_name, latest_version = result
            version_map[package_name] = latest_version
        
        return version_map