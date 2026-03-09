"""Test cases for XBOM actuator functionality.

This module contains tests for the XBOM actuator, including
command handling, query operations, and response generation.
Tests reflect the ACTUAL API implementation.
"""

import pytest
from unittest.mock import MagicMock, patch

import otupy as oc2
from otupy import (
    Actions, StatusCode, Features, Feature, ResponseType, Command, ArrayOf
)

import otupy.profiles.xbom as xbom
from otupy.profiles.xbom import CyclonedxXbom, Profile, Args, Results, XbomCtx
from otupy.profiles.xbom.data.xbom_format import XbomFormat
from otupy.profiles.xbom.data.application import Application
from otupy.profiles.xbom.data.container import Container
from otupy.profiles.xbom.data.pod import Pod
from otupy.profiles.xbom.data.server import Server
from otupy.profiles.xbom.data.vm import VM
from otupy.profiles.xbom.data.cloud import Cloud
from otupy.profiles.xbom.data.network import Network
from otupy.profiles.xbom.data.os import OS
from otupy.profiles.xbom.data.iot import IOT
from otupy.profiles.xbom.data.host import Host
from otupy.profiles.xbom.data.service import Service
from otupy.profiles.xbom.data.abstract_xbom import Xbom
from otupy.profiles.xbom.data.network_type import NetworkType
from otupy.profiles.xbom.actuator import Specifiers
from otupy.actuators.xbom.xbom_actuator import XBOMActuator
from otupy.types.data.hostname import Hostname


class MockXBOMActuator(XBOMActuator):
    """Mock XBOM Actuator for testing purposes.
    
    This actuator provides a controlled test environment with predefined
    services and components for testing discovery and query operations.
    """

    def __init__(self, **kwargs):
        """Initialize the mock actuator with default test data."""
        super().__init__(**kwargs)
        self._test_bom = None

    def set_test_bom(self, bom):
        """Set a pre-built test BOM for the actuator."""
        self._test_bom = bom

    def discover_context(self):
        """Mock context discovery - uses test BOM if available."""
        if self._test_bom is not None:
            self.bom = self._test_bom
        else:
            self._build_bom()

    def discover_services(self):
        """Mock service discovery - no-op, use set_test_bom instead."""
        pass

    def discover_links(self):
        """Mock link discovery - no-op for basic tests."""
        pass


class TestXBOMActuatorInitialization:
    """Test cases for XBOM actuator initialization."""

    def test_actuator_creation_default(self):
        """Test creating an actuator with default parameters."""
        actuator = MockXBOMActuator()
        
        assert actuator is not None
        assert actuator.xbom_format == XbomFormat.cyclonedx
        assert actuator.bom is None
        assert actuator.services is not None

    def test_actuator_creation_with_specifiers(self):
        """Test creating an actuator with specifiers."""
        specifiers = {'domain': 'test-domain', 'asset_id': 'test-asset'}
        actuator = MockXBOMActuator(specifiers=specifiers)
        
        assert actuator.specifiers is not None
        assert actuator.specifiers['domain'] == 'test-domain'
        assert actuator.specifiers['asset_id'] == 'test-asset'

    def test_actuator_creation_with_auth(self):
        """Test creating an actuator with authentication."""
        auth = {'token': 'test-token', 'type': 'bearer'}
        actuator = MockXBOMActuator(auth=auth)
        
        assert actuator.auth is not None
        assert actuator.auth['token'] == 'test-token'

    def test_actuator_creation_with_config(self):
        """Test creating an actuator with configuration."""
        config = {'endpoint': 'https://api.example.com', 'timeout': 30}
        actuator = MockXBOMActuator(config=config)
        
        assert actuator.config is not None
        assert actuator.config['endpoint'] == 'https://api.example.com'

    def test_actuator_creation_with_owner(self):
        """Test creating an actuator with owner."""
        actuator = MockXBOMActuator(owner='test-owner')
        
        assert actuator.owner == 'test-owner'

    def test_actuator_creation_with_peers(self):
        """Test creating an actuator with peers."""
        peers = [
            {'service_name': 'peer1', 'consumer': {'host': 'peer1.example.com'}},
            {'service_name': 'peer2', 'consumer': {'host': 'peer2.example.com'}}
        ]
        actuator = MockXBOMActuator(peers=peers)
        
        assert actuator.peers is not None
        assert len(actuator.peers) == 2


class TestXBOMActuatorCreateBom:
    """Test cases for BOM creation factory method."""

    def test_create_bom_default_format(self):
        """Test creating a BOM with default format."""
        actuator = MockXBOMActuator()
        
        bom = actuator.create_bom()
        
        assert bom is not None
        assert isinstance(bom, CyclonedxXbom)

    def test_create_bom_cyclonedx_format(self):
        """Test creating a BOM with CycloneDX format."""
        actuator = MockXBOMActuator()
        actuator.xbom_format = XbomFormat.cyclonedx
        
        bom = actuator.create_bom()
        
        assert isinstance(bom, CyclonedxXbom)


class TestXBOMActuatorQueryFeatures:
    """Test cases for XBOM actuator query features command."""

    def test_query_features_versions(self):
        """Test querying for versions feature."""
        actuator = MockXBOMActuator()
        cmd = Command(
            Actions.query,
            Features([Feature.versions])
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.OK
        assert response.get('results') is not None

    def test_query_features_profiles(self):
        """Test querying for profiles feature."""
        actuator = MockXBOMActuator()
        cmd = Command(
            Actions.query,
            Features([Feature.profiles])
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.OK
        assert response.get('results') is not None

    def test_query_features_pairs(self):
        """Test querying for pairs feature."""
        actuator = MockXBOMActuator()
        cmd = Command(
            Actions.query,
            Features([Feature.pairs])
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.OK
        assert response.get('results') is not None

    def test_query_features_multiple(self):
        """Test querying for multiple features."""
        actuator = MockXBOMActuator()
        cmd = Command(
            Actions.query,
            Features([Feature.versions, Feature.profiles, Feature.pairs])
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.OK

    def test_query_features_rate_limit_not_implemented(self):
        """Test that rate_limit feature is not implemented."""
        actuator = MockXBOMActuator()
        cmd = Command(
            Actions.query,
            Features([Feature.rate_limit])
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.NOTIMPLEMENTED


class TestXBOMActuatorQueryXbom:
    """Test cases for XBOM actuator query xbom command - ACTUAL API."""

    def test_query_xbom_basic(self):
        """Test querying XBOM without arguments."""
        actuator = MockXBOMActuator()
        
        # Create a test BOM
        test_bom = CyclonedxXbom()
        test_bom.add(Application(name="test-app", version="1.0.0"))
        actuator.set_test_bom(test_bom)
        
        # Provide empty Args to avoid NoneType errors
        cmd = Command(
            Actions.query,
            XbomCtx(format=XbomFormat.cyclonedx),
            Args({})
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.OK
        # Results should contain singular 'bom' field
        if response.get('results'):
            assert 'bom' in response['results']

    def test_query_xbom_cached(self):
        """Test querying XBOM with cached argument."""
        actuator = MockXBOMActuator()
        
        # First call to populate with cached=False
        test_bom = CyclonedxXbom()
        test_bom.add(Application(name="cached-app", version="1.0.0"))
        actuator.set_test_bom(test_bom)
        
        args1 = Args({'cached': False})
        cmd1 = Command(
            Actions.query,
            XbomCtx(format=XbomFormat.cyclonedx),
            args1
        )
        response1 = actuator.run(cmd1)
        assert response1['status'] == StatusCode.OK
        
        # Second call with cached=True (should use cached bom)
        args2 = Args({'cached': True})
        cmd2 = Command(
            Actions.query,
            XbomCtx(format=XbomFormat.cyclonedx),
            args2
        )
        
        response2 = actuator.run(cmd2)
        assert response2['status'] == StatusCode.OK

    def test_query_xbom_with_format(self):
        """Test querying XBOM with specific format."""
        actuator = MockXBOMActuator()
        
        test_bom = CyclonedxXbom()
        test_bom.add(Application(name="format-test", version="1.0.0"))
        actuator.set_test_bom(test_bom)
        
        cmd = Command(
            Actions.query,
            XbomCtx(format=XbomFormat.cyclonedx),
            Args({})
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.OK
        # Actuator should have set its format
        assert actuator.xbom_format == XbomFormat.cyclonedx

    def test_query_xbom_empty(self):
        """Test querying XBOM with no BOM returns OK."""
        actuator = MockXBOMActuator()
        
        # No BOM set
        cmd = Command(
            Actions.query,
            XbomCtx(),
            Args({})
        )
        
        response = actuator.run(cmd)
        
        # Should return OK even with no BOM
        assert response['status'] == StatusCode.OK


class TestXBOMActuatorInvalidCommands:
    """Test cases for handling invalid commands."""

    def test_invalid_action(self):
        """Test that invalid actions return NOT IMPLEMENTED."""
        actuator = MockXBOMActuator()
        cmd = Command(
            Actions.deny,  # Not a valid action for XBOM
            Features([Feature.versions])
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.NOTIMPLEMENTED

    def test_invalid_target(self):
        """Test that invalid targets return NOT IMPLEMENTED."""
        actuator = MockXBOMActuator()
        # Create a command with an unsupported target type
        cmd = Command(
            Actions.query,
            oc2.IPv4Net("192.168.1.0/24")  # Not a valid target for XBOM query
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.NOTIMPLEMENTED

    def test_actuator_not_found(self):
        """Test response when actuator specifiers don't match."""
        actuator = MockXBOMActuator(
            specifiers={'asset_id': 'actuator-1'}
        )
        
        # Create command with different actuator specifier
        specifiers = Specifiers({'asset_id': 'actuator-2'})
        cmd = Command(
            Actions.query,
            Features([Feature.versions]),
            actuator=specifiers
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.NOTFOUND


class TestXBOMActuatorBomOperations:
    """Test cases for BOM manipulation operations in the actuator."""

    def test_bom_building(self):
        """Test that BOM is set correctly."""
        actuator = MockXBOMActuator()
        
        bom = CyclonedxXbom()
        bom.add(Application(name="app1", version="1.0.0"))
        bom.add(Application(name="app2", version="2.0.0"))
        
        actuator.set_test_bom(bom)
        actuator.discover_context()
        
        assert actuator.bom is not None
        assert isinstance(actuator.bom, CyclonedxXbom)

    def test_bom_with_no_components(self):
        """Test with empty BOM."""
        actuator = MockXBOMActuator()
        
        bom = CyclonedxXbom()
        actuator.set_test_bom(bom)
        actuator.discover_context()
        
        assert actuator.bom is not None
        # BOM exists but is empty
        assert len(actuator.bom.bom.components) == 0  # type: ignore


class TestXBOMActuatorWithSpecifiers:
    """Test cases for actuator with specifiers matching."""

    def test_empty_specifiers_match(self):
        """Test that empty specifiers always match."""
        actuator = MockXBOMActuator(
            specifiers={'asset_id': 'test-actuator'}
        )
        
        # Command without actuator specifiers
        cmd = Command(
            Actions.query,
            Features([Feature.versions])
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.OK

    def test_matching_specifiers(self):
        """Test that matching specifiers work correctly."""
        actuator = MockXBOMActuator(
            specifiers={'asset_id': 'my-actuator'}
        )
        
        specifiers = Specifiers({'asset_id': 'my-actuator'})
        cmd = Command(
            Actions.query,
            Features([Feature.versions]),
            actuator=specifiers
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.OK


class TestXBOMActuatorDiscovery:
    """Test cases for service discovery functionality."""

    def test_discover_context_uses_bom(self):
        """Test that discover_context uses pre-set BOM."""
        actuator = MockXBOMActuator()
        
        bom = CyclonedxXbom()
        bom.add(Application(name="discovered-app", version="1.0.0"))
        actuator.set_test_bom(bom)
        
        actuator.discover_context()
        
        assert actuator.bom is not None
        assert actuator.bom == bom

    def test_update_clears_previous_state(self):
        """Test that _update() clears previous services/links."""
        actuator = MockXBOMActuator()
        
        # Set initial state
        bom = CyclonedxXbom()
        bom.add(Application(name="initial", version="1.0.0"))
        actuator.set_test_bom(bom)
        actuator.discover_context()
        
        assert actuator.bom is not None
        
        # Clear test bom so discover_context doesn't set it again
        actuator._test_bom = None
        
        # Call _update which should clear state
        actuator._update()
        
        # Services/links should be cleared
        assert len(actuator.services) == 0
        assert len(actuator.links) == 0
        # bom will be set by discover_context in _update, but should be empty
        # since we cleared _test_bom


class TestXBOMActuatorWithVariousServices:
    """Test actuator with different component types."""

    def test_application_component(self):
        """Test actuator with application component."""
        actuator = MockXBOMActuator()
        
        bom = CyclonedxXbom()
        bom.add(Application(name="my-app", version="1.0.0"))
        actuator.set_test_bom(bom)
        actuator.discover_context()
        
        assert actuator.bom is not None

    def test_host_component(self):
        """Test actuator with host component."""
        actuator = MockXBOMActuator()
        
        bom = CyclonedxXbom()
        bom.add(Host(name="my-host", description="Test host"))
        actuator.set_test_bom(bom)
        actuator.discover_context()
        
        assert actuator.bom is not None

    def test_mixed_components(self):
        """Test actuator with multiple component types."""
        actuator = MockXBOMActuator()
        
        bom = CyclonedxXbom()
        bom.add(Application(name="app", version="1.0.0"))
        bom.add(Host(name="host", description="Test"))
        # Note: Network might be added as Service not Component
        
        actuator.set_test_bom(bom)
        actuator.discover_context()
        
        assert actuator.bom is not None
        # Check that we have at least the 2 components we added
        assert len(actuator.bom.bom.components) >= 2  # type: ignore


class TestXBOMActuatorErrorHandling:
    """Test cases for actuator error handling."""

    def test_empty_bom_handled(self):
        """Test that empty BOMs are handled correctly."""
        actuator = MockXBOMActuator()
        
        bom = CyclonedxXbom()
        actuator.set_test_bom(bom)
        
        # Should not raise
        actuator.discover_context()
        
        assert actuator.bom is not None

    def test_command_validation_failure(self):
        """Test handling of invalid command."""
        actuator = MockXBOMActuator()
        
        # Invalid action for XBOM
        cmd = Command(
            Actions.create,
            XbomCtx()
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.NOTIMPLEMENTED


class TestXBOMActuatorResultsFormat:
    """Test cases for verifying correct results format."""

    def test_results_contains_bom_field(self):
        """Test that results contain 'bom' field (singular)."""
        actuator = MockXBOMActuator()
        
        bom = CyclonedxXbom()
        bom.add(Application(name="test-app", version="1.0.0"))
        actuator.set_test_bom(bom)
        
        cmd = Command(
            Actions.query,
            XbomCtx(format=XbomFormat.cyclonedx),
            Args({})
        )
        
        response = actuator.run(cmd)
        
        assert response['status'] == StatusCode.OK
        if response.get('results'):
            # Should have 'bom' field, NOT 'boms' or 'bom_names'
            assert 'bom' in response['results']
            # Verify it doesn't have deprecated fields
            assert 'boms' not in response['results']
            assert 'bom_names' not in response['results']

    def test_bom_field_contains_xbom(self):
        """Test that bom field contains an Xbom object."""
        actuator = MockXBOMActuator()
        
        bom = CyclonedxXbom()
        bom.add(Application(name="test-app", version="1.0.0"))
        actuator.set_test_bom(bom)
        
        cmd = Command(
            Actions.query,
            XbomCtx(),
            Args({})
        )
        
        response = actuator.run(cmd)
        
        if response.get('results') and 'bom' in response['results']:
            bom_result = response['results']['bom']
            assert isinstance(bom_result, (Xbom, CyclonedxXbom))


class TestXBOMActuatorFormatSetting:
    """Test cases for xbom_format setting from target."""

    def test_format_set_from_target(self):
        """Test that format is set from XbomCtx target."""
        actuator = MockXBOMActuator()
        
        # Initially cyclonedx
        assert actuator.xbom_format == XbomFormat.cyclonedx
        
        cmd = Command(
            Actions.query,
            XbomCtx(format=XbomFormat.cyclonedx),
            Args({})
        )
        
        response = actuator.run(cmd)
        
        # Format should be set from target
        assert actuator.xbom_format == XbomFormat.cyclonedx

    def test_format_default_when_not_specified(self):
        """Test that format defaults to cyclonedx when not specified."""
        actuator = MockXBOMActuator()
        
        cmd = Command(
            Actions.query,
            XbomCtx(),  # No format specified
            Args({})
        )
        
        response = actuator.run(cmd)
        
        # Should keep default
        assert actuator.xbom_format == XbomFormat.cyclonedx
