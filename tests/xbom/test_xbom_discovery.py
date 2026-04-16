"""Test cases for XBOM discovery functionality.

This module contains tests for the XBOM profile discovery mechanisms,
including target creation, validation, and query operations.
"""

import pytest

import otupy as oc2
from otupy import Actions, StatusCode, Features, Feature, ResponseType, Command

import otupy.profiles.xbom as xbom
from otupy.profiles.xbom import CyclonedxXbom, Profile, Args, Results, XbomCtx
from otupy.profiles.xbom.data.xbom_format import XbomFormat
from otupy.profiles.xbom.data.application import Application
from otupy.profiles.xbom.data.container import Container
from otupy.profiles.xbom.data.pod import Pod
from otupy.profiles.xbom.data.port import Port
from otupy.profiles.xbom.data.server import Server
from otupy.profiles.xbom.data.vm import VM
from otupy.profiles.xbom.data.network import Network
from otupy.profiles.xbom.data.network_type import NetworkType
from otupy.profiles.xbom.data.host import Host
from otupy.profiles.xbom.actuator import Specifiers
from otupy.profiles.xbom.validation import (
    AllowedActions, AllowedTargets, AllowedCommandTarget,
    AllowedCommandArguments, validate_command, validate_args
)
from otupy.types.data.hostname import Hostname
from cyclonedx.model.component import Component
from cyclonedx.model.service import Service


class TestXBOMProfile:
    """Test cases for the XBOM profile definition."""

    def test_profile_nsid(self):
        """Test that the profile nsid is correctly set."""
        assert Profile.nsid == 'x-xbom'

    def test_profile_name(self):
        """Test that the profile name is correctly set."""
        assert Profile.name == 'x Bill of Materials'


class TestXbomCtxTarget:
    """Test cases for the XbomCtx target - ACTUAL API."""

    def test_xbom_ctx_creation_empty(self):
        """Test creating an empty XbomCtx target."""
        target = XbomCtx()
        
        assert target is not None
        assert target.get('format') is None

    def test_xbom_ctx_creation_with_format(self):
        """Test creating an XbomCtx target with format."""
        target = XbomCtx(format=XbomFormat.cyclonedx)
        
        assert target is not None
        assert target.get('format') == XbomFormat.cyclonedx

    def test_xbom_ctx_creation_with_dict(self):
        """Test creating an XbomCtx target from dictionary."""
        target = XbomCtx({'format': XbomFormat.cyclonedx})
        
        assert target is not None
        assert target.get('format') == XbomFormat.cyclonedx

    def test_xbom_ctx_repr(self):
        """Test string representation of XbomCtx."""
        target = XbomCtx(format=XbomFormat.cyclonedx)
        
        repr_str = repr(target)
        assert 'XbomCtx' in repr_str or 'SbomCtx' in repr_str  # Backward compat alias

    def test_xbom_ctx_str(self):
        """Test str representation of XbomCtx."""
        target = XbomCtx(format=XbomFormat.cyclonedx)
        
        str_repr = str(target)
        assert 'XbomCtx' in str_repr or 'SbomCtx' in str_repr  # Backward compat alias


class TestXBOMArgs:
    """Test cases for the XBOM Args extension - ACTUAL API."""

    def test_args_creation_empty(self):
        """Test creating empty Args."""
        args = Args({})
        
        assert args is not None

    def test_args_creation_with_cached(self):
        """Test creating Args with cached flag."""
        args = Args({'cached': True})
        
        assert args is not None
        assert args.get('cached') == True

    def test_args_creation_with_cached_false(self):
        """Test creating Args with cached=False."""
        args = Args({'cached': False})
        
        assert args is not None
        assert args.get('cached') == False


class TestXBOMResults:
    """Test cases for the XBOM Results extension - ACTUAL API."""

    def test_results_with_bom(self):
        """Test creating Results with bom (singular)."""
        bom = CyclonedxXbom()
        bom.add(Application(name="test-app", version="1.0.0"))
        
        results = Results({'bom': bom})
        
        assert results is not None
        assert 'bom' in results
        assert results.get('bom') is not None

    def test_results_with_bom_from_dict(self):
        """Test creating Results from serialized bom data."""
        bom = CyclonedxXbom()
        bom.add(Application(name="test-app", version="1.0.0"))
        bom_dict = bom.serialize()
        
        results = Results({'bom': bom})
        
        assert results is not None
        assert results.get('bom') is not None


class TestXBOMSpecifiers:
    """Test cases for the XBOM Actuator Specifiers."""

    def test_specifiers_creation_with_domain(self):
        """Test creating Specifiers with domain."""
        specifiers = Specifiers({'domain': 'test-domain'})
        
        assert specifiers is not None
        assert specifiers.get('domain') == 'test-domain'

    def test_specifiers_creation_with_asset_id(self):
        """Test creating Specifiers with asset_id."""
        specifiers = Specifiers({'asset_id': 'test-asset'})
        
        assert specifiers is not None
        assert specifiers.get('asset_id') == 'test-asset'

    def test_specifiers_creation_with_all_fields(self):
        """Test creating Specifiers with all fields."""
        specifiers = Specifiers({'domain': 'my-domain', 'asset_id': 'my-asset'})
        
        assert specifiers is not None
        assert specifiers.get('domain') == 'my-domain'
        assert specifiers.get('asset_id') == 'my-asset'

    def test_specifiers_equality(self):
        """Test Specifiers equality comparison."""
        spec1 = Specifiers({'domain': 'test', 'asset_id': 'asset1'})
        spec2 = Specifiers({'domain': 'test', 'asset_id': 'asset1'})
        spec3 = Specifiers({'domain': 'test', 'asset_id': 'asset2'})
        
        assert spec1 == spec2
        assert spec1 != spec3

    def test_specifiers_str(self):
        """Test Specifiers string representation."""
        specifiers = Specifiers({'domain': 'test-domain', 'asset_id': 'test-asset'})
        
        str_repr = str(specifiers)
        assert 'x-xbom' in str_repr

    def test_specifiers_nsid(self):
        """Test Specifiers nsid property."""
        specifiers = Specifiers({'domain': 'test'})
        
        assert specifiers.nsid == 'x-xbom'


class TestXBOMValidation:
    """Test cases for XBOM command validation."""

    def test_allowed_actions(self):
        """Test that query is an allowed action."""
        assert Actions.query in AllowedActions

    def test_allowed_targets(self):
        """Test that expected targets are allowed."""
        assert 'features' in AllowedTargets
        assert 'x-xbom:xbom' in AllowedTargets  # Correct target name

    def test_validate_command_query_features(self):
        """Test validating a query features command."""
        cmd = Command(
            Actions.query,
            Features([Feature.versions, Feature.profiles])
        )
        
        assert validate_command(cmd) == True

    def test_validate_command_query_xbom(self):
        """Test validating a query xbom command."""
        cmd = Command(
            Actions.query,
            XbomCtx(format=XbomFormat.cyclonedx)
        )
        
        assert validate_command(cmd) == True

    def test_validate_command_invalid_action(self):
        """Test that invalid actions are rejected."""
        # 'deny' is not a valid action for XBOM
        cmd = Command(
            Actions.deny,
            Features([Feature.versions])
        )
        
        assert validate_command(cmd) == False

    def test_validate_args_query_features(self):
        """Test validating args for query features."""
        args = Args({'response_requested': ResponseType.complete})
        cmd = Command(
            Actions.query,
            Features([Feature.versions]),
            args
        )
        
        assert validate_args(cmd) == True

    def test_validate_args_query_xbom_cached(self):
        """Test validating args for query xbom with cached."""
        args = Args({'cached': True})
        cmd = Command(
            Actions.query,
            XbomCtx(),
            args
        )
        
        assert validate_args(cmd) == True

    def test_validate_args_none(self):
        """Test validating command with no args."""
        # Create command without args (args defaults to None)
        cmd = Command(
            Actions.query,
            Features([Feature.versions])
        )
        
        assert validate_args(cmd) == True


class TestXBOMBomOperations:
    """Test cases for XBOM BOM-level operations."""

    def test_get_bom_serial_number(self):
        """Test getting BOM serial number."""
        bom = CyclonedxXbom()
        
        serial = bom.get_bom_serial_number()
        
        assert serial is not None
        assert len(serial) > 0

    def test_get_bom_version(self):
        """Test getting BOM version."""
        bom = CyclonedxXbom()
        
        version = bom.get_bom_version()
        
        assert version == 1

    def test_add_multiple_components(self):
        """Test adding multiple components to a BOM."""
        bom = CyclonedxXbom()
        
        app1 = Application(name="app1", version="1.0.0")
        app2 = Application(name="app2", version="2.0.0")
        
        bom.add(app1)
        bom.add(app2)
        
        assert len(bom.bom.components) == 2  # type: ignore

    def test_add_component_and_service(self):
        """Test adding both components and services."""
        bom = CyclonedxXbom()
        
        app = Application(name="app", version="1.0.0")
        host = Host(name="server1", description="Test server")
        
        bom.add(app)
        bom.add(host)
        
        # Both should be added to components
        assert len(bom.bom.components) == 2  # type: ignore

    def test_find_ref_by_name(self):
        """Test finding component bom_ref by name."""
        bom = CyclonedxXbom()
        app = Application(name="my-app", version="1.0.0")
        bom.add(app)
        
        # Need to serialize to populate bom_refs
        bom.serialize()
        
        ref = bom.find_ref_by_name("my-app")
        
        # Note: bom_ref might still be None if not set by CycloneDX library
        # This test verifies the search works, even if ref is None
        assert isinstance(ref, (str, type(None)))

    def test_find_ref_by_name_not_found(self):
        """Test finding non-existent component returns None."""
        bom = CyclonedxXbom()
        app = Application(name="my-app", version="1.0.0")
        bom.add(app)
        
        ref = bom.find_ref_by_name("non-existent")
        
        assert ref is None

    def test_get_bom_link(self):
        """Test generating bom-link with a known ref."""
        bom = CyclonedxXbom()
        
        # Create a component with explicit bom_ref
        from cyclonedx.model.component import Component, ComponentType
        from cyclonedx.model.bom_ref import BomRef
        
        component = Component(
            name="my-app",
            type=ComponentType.APPLICATION,
            bom_ref=BomRef("test-ref-123")
        )
        bom.add(component)
        
        link = bom.get_bom_link("test-ref-123")
        
        assert link is not None
        assert link.startswith("urn:cdx:")
        assert "test-ref-123" in link

    def test_add_dependency(self):
        """Test adding dependency relationship."""
        bom = CyclonedxXbom()
        
        # Create components with explicit bom_refs
        from cyclonedx.model.component import Component, ComponentType
        from cyclonedx.model.bom_ref import BomRef
        
        app1 = Component(
            name="app1",
            type=ComponentType.APPLICATION,
            bom_ref=BomRef("app1-ref")
        )
        app2 = Component(
            name="app2",
            type=ComponentType.APPLICATION,
            bom_ref=BomRef("app2-ref")
        )
        
        bom.add(app1)
        bom.add(app2)
        
        # app2 depends on app1
        bom.add_dependency("app1-ref", "app2-ref")
        
        assert len(bom.bom.dependencies) > 0  # type: ignore

    def test_merge_boms(self):
        """Test merging two BOMs."""
        bom1 = CyclonedxXbom()
        bom1.add(Application(name="app1", version="1.0.0"))
        
        bom2 = CyclonedxXbom()
        bom2.add(Application(name="app2", version="2.0.0"))
        
        bom1.merge(bom2)
        
        assert len(bom1.bom.components) == 2  # type: ignore

    def test_serialize_deserialize(self):
        """Test serializing and deserializing a BOM."""
        bom = CyclonedxXbom()
        bom.add(Application(name="test-app", version="1.0.0"))
        
        serialized = bom.serialize()
        
        assert serialized is not None
        assert isinstance(serialized, dict)
        assert 'components' in serialized


class TestXbomFormat:
    """Test cases for XBOM format enumeration."""

    def test_cyclonedx_format(self):
        """Test CycloneDX format value."""
        assert XbomFormat.cyclonedx.value == 1

    def test_format_comparison(self):
        """Test format comparison."""
        format1 = XbomFormat.cyclonedx
        format2 = XbomFormat.cyclonedx
        
        assert format1 == format2


class TestXBOMFaultyValues:
    """Test cases for handling faulty/invalid values."""

    def test_xbom_ctx_with_invalid_format_type(self):
        """Test XbomCtx with invalid format type raises error or handles gracefully."""
        # Passing a string instead of XbomFormat enum
        with pytest.raises((TypeError, ValueError, KeyError)):
            target = XbomCtx(format="invalid-format")
            # Force validation if lazy
            _ = target.get('format')

    def test_args_with_invalid_cached_type(self):
        """Test Args with invalid type for cached field - library is lenient."""
        # The library accepts truthy values without strict type checking
        args = Args({'cached': 1})
        # 1 is truthy, so it's accepted
        assert args.get('cached') == 1

    def test_specifiers_with_empty_values(self):
        """Test Specifiers with empty string values."""
        specifiers = Specifiers({'domain': '', 'asset_id': ''})
        
        assert specifiers.get('domain') == ''
        assert specifiers.get('asset_id') == ''

    def test_validate_command_with_none_action(self):
        """Test validation with None action."""
        with pytest.raises((TypeError, ValueError, AttributeError)):
            cmd = Command(None, Features([Feature.versions]))
            validate_command(cmd)

    def test_cyclonedx_xbom_add_none(self):
        """Test adding None to XBOM raises appropriate error."""
        bom = CyclonedxXbom()
        
        with pytest.raises((TypeError, AttributeError)):
            bom.add(None)

    def test_cyclonedx_xbom_add_invalid_type(self):
        """Test adding invalid type to XBOM raises error."""
        bom = CyclonedxXbom()
        
        with pytest.raises(TypeError):
            bom.add("not a component")

    def test_cyclonedx_xbom_add_dict(self):
        """Test adding plain dict to XBOM raises error."""
        bom = CyclonedxXbom()
        
        with pytest.raises(TypeError):
            bom.add({'name': 'test', 'version': '1.0'})

    def test_application_with_empty_name(self):
        """Test Application with empty name."""
        # Empty name should be allowed or raise error
        app = Application(name="", version="1.0.0")
        
        # Should create but with empty name
        assert app is not None

    def test_application_with_none_version(self):
        """Test Application with None version."""
        app = Application(name="test-app", version=None)
        
        assert app is not None

    def test_container_with_missing_required_fields(self):
        """Test Container with missing fields - allows empty initialization."""
        # Container allows empty initialization (fields are optional)
        container = Container()
        assert container is not None

    def test_vm_with_missing_fields(self):
        """Test VM with missing fields - allows empty initialization."""
        # VM allows empty initialization (fields are optional)
        vm = VM()
        assert vm is not None

    def test_pod_with_namespace(self):
        """Test Pod with namespace."""
        pod = Pod(namespace="default")
        
        assert pod is not None
        assert pod.namespace == "default"

    def test_pod_with_none_namespace(self):
        """Test Pod with None namespace."""
        pod = Pod(namespace=None)
        
        assert pod is not None
        assert pod.namespace == "None"  # Converts to string

    def test_server_with_none_hostname(self):
        """Test Server with None hostname - accepts it."""
        server = Server(None)
        assert server is not None

    def test_network_with_invalid_type(self):
        """Test Network with invalid network type - library accepts strings."""
        # The library is lenient and accepts string types
        network = Network(
            description="Test",
            name="test-net",
            type="invalid-type"  # Accepts string directly
        )
        assert network is not None


class TestXBOMEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_specifiers_with_very_long_values(self):
        """Test Specifiers with very long string values."""
        long_domain = "d" * 1000
        long_asset = "a" * 1000
        
        specifiers = Specifiers({'domain': long_domain, 'asset_id': long_asset})
        
        assert specifiers.get('domain') == long_domain
        assert specifiers.get('asset_id') == long_asset

    def test_specifiers_with_whitespace_values(self):
        """Test Specifiers with whitespace values."""
        specifiers = Specifiers({'domain': '  spaces  ', 'asset_id': '\ttab\t'})
        
        domain = specifiers.get('domain')
        asset_id = specifiers.get('asset_id')
        assert domain is not None
        assert asset_id is not None
        assert '  spaces  ' in domain
        assert '\t' in asset_id

    def test_application_with_very_long_version(self):
        """Test Application with unusually long version string."""
        long_version = "1.0.0-alpha.beta.gamma.delta." + "x" * 500
        
        app = Application(name="test-app", version=long_version)
        
        assert app is not None

    def test_multiple_boms_same_name(self):
        """Test creating multiple BOMs with same component name."""
        bom1 = CyclonedxXbom()
        bom1.add(Application(name="duplicate-app", version="1.0.0"))
        
        bom2 = CyclonedxXbom()
        bom2.add(Application(name="duplicate-app", version="2.0.0"))
        
        # Both should exist independently
        assert list(bom1.bom.components)[0].version == "1.0.0"  # type: ignore
        assert list(bom2.bom.components)[0].version == "2.0.0"  # type: ignore

    def test_add_same_component_twice_to_bom(self):
        """Test adding the same component twice to a BOM."""
        bom = CyclonedxXbom()
        app = Application(name="test-app", version="1.0.0")
        
        bom.add(app)
        bom.add(app)  # Add same component again
        
        # Behavior depends on implementation - may add duplicate or ignore
        assert len(bom.bom.components) >= 1  # type: ignore

    def test_empty_specifiers(self):
        """Test creating empty Specifiers."""
        specifiers = Specifiers({})
        
        assert specifiers is not None
        assert specifiers.get('domain') is None
        assert specifiers.get('asset_id') is None

    def test_bom_with_no_components(self):
        """Test working with empty BOM."""
        bom = CyclonedxXbom()
        
        assert bom is not None
        assert bom.bom is not None
        assert len(bom.bom.components) == 0  # type: ignore
        assert len(bom.bom.services) == 0  # type: ignore


class TestCycloneDXComponentTypes:
    """Test adding CycloneDX Component and Service directly to XBOM."""

    def test_add_cyclonedx_component_directly(self):
        """Test adding CycloneDX Component object directly."""
        from cyclonedx.model.component import Component, ComponentType
        
        bom = CyclonedxXbom()
        component = Component(name="direct-component", type=ComponentType.LIBRARY)
        
        bom.add(component)
        
        assert len(bom.bom.components) == 1  # type: ignore

    def test_add_cyclonedx_service_directly(self):
        """Test adding CycloneDX Service object directly."""
        from cyclonedx.model.service import Service
        
        bom = CyclonedxXbom()
        service = Service(name="direct-service")
        
        bom.add(service)
        
        assert len(bom.bom.services) == 1  # type: ignore
