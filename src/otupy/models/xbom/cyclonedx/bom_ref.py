"""BOM Reference Generator

This module provides centralized bom_ref generation for CycloneDX components and services.
All xbom profile data types should use this module to generate consistent bom_refs.

To change the bom_ref generation strategy, modify the generate_bom_ref function.
"""

from uuid import uuid4


def generate_bom_ref(prefix: str) -> str:
    """Generate a unique bom_ref for CycloneDX components or services.
    
    This centralized function ensures consistent bom_ref generation across all
    XBOM profile data types. Modify this function to change the bom_ref format
    globally.
    
    Args:
        prefix: The type prefix for the bom_ref (e.g., 'container', 'service', 'vm').
    
    Returns:
        str: A unique bom_ref string in the format "{prefix}-{uuid}".
    
    Examples:
        >>> generate_bom_ref("container")  # Returns "container-<uuid>"
        >>> generate_bom_ref("service")  # Returns "service-<uuid>"
    """
    return f"{prefix}-{uuid4()}"


def generate_uuid() -> str:
    """Generate a UUID string.
    
    This function is provided for cases where only a UUID is needed
    without a prefix.
    
    Returns:
        str: A UUID string.
    """
    return str(uuid4())
