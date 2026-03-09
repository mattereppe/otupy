from otupy.profiles.xbom import CyclonedxXbom
from otupy.profiles.xbom.data.application import Application
from otupy.profiles.xbom.data.cloud import Cloud
from otupy.profiles.xbom.data.host import Host
from otupy.profiles.xbom.data.container import Container
from otupy.profiles.xbom.data.iot import IOT
from otupy.profiles.xbom.data.network import Network
from otupy.profiles.xbom.data.os import OS
from otupy.profiles.xbom.data.server import Server
from otupy.profiles.xbom.data.vm import VM
from otupy.profiles.xbom.data.web_service import WebService
from otupy.profiles.xbom.data.pod import Pod

from cyclonedx.model.component import ComponentType
from cyclonedx.model.service import Service as CycloneDXService

from otupy.types.data.hostname import Hostname
from otupy.profiles.xbom.data.network_type import NetworkType

class TestXBOMCreation:
    """Test cases for XBOM creation and initialization."""

    def test_create_empty_xbom(self):
        """Test creating an empty XBOM instance."""
        bom = CyclonedxXbom()

        assert bom is not None
        assert len(bom.bom.services) == 0  # type: ignore
        assert len(bom.bom.components) == 0  # type: ignore
    
    def test_application_insertion_as_cyclonedx(self):
        """Test inserting a component into the XBOM as CycloneDX format."""
        bom = CyclonedxXbom()
        component = Application(
            name="test-component",
            version="1.0.0"
        ).as_cyclonedx()
        bom.add(component)

        assert component is not None
        assert len(bom.bom.components) == 1  # type: ignore
        assert bom.bom.components[0].name == "test-component"  # type: ignore
        assert bom.bom.components[0].type == ComponentType.APPLICATION  # type: ignore

    def test_application_insertion_as_application(self):
        """Test inserting an Application component into the XBOM."""
        bom = CyclonedxXbom()
        app = Application(
            name="test-application",
            version="1.0.0"
        )
        bom.add(app)

        assert app is not None
        assert len(bom.bom.components) == 1  # type: ignore
        component = list(bom.bom.components)[0]  # type: ignore
        assert component.name == "test-application"
        assert component.version == "1.0.0"
        assert component.type == ComponentType.APPLICATION
        
        # Validate BOM reference is set
        assert component.bom_ref is not None
    
    def test_vm_insertion_as_cyclonedx(self):
        """Test inserting a VM component into the XBOM as CycloneDX format."""
        bom = CyclonedxXbom()
        # VM now only takes hypervisor, hypervisor_type, and image params - no name/id/description
        component = VM(
            image="test-image",
            hypervisor="QEMU"
        ).as_cyclonedx()
        bom.add(component)

        assert component is not None
        assert len(bom.bom.components) == 1  # type: ignore
        assert bom.bom.components[0].type == ComponentType.PLATFORM  # type: ignore

    def test_vm_insertion_as_vm(self):
        """Test inserting a VM component into the XBOM."""
        bom = CyclonedxXbom()
        vm = VM(
            image="test-image",
            hypervisor="QEMU"
        )
        bom.add(vm)

        assert vm is not None
        assert len(bom.bom.components) == 1  # type: ignore
        component = list(bom.bom.components)[0]  # type: ignore
        assert component.type == ComponentType.PLATFORM
        
        # Validate all properties are set correctly
        assert component.properties is not None
        properties_dict = {prop.name: prop.value for prop in component.properties}
        assert properties_dict.get("otupy:type") == "virtual_machine"
        assert properties_dict.get("otupy:vm:image") == "test-image"
        assert properties_dict.get("otupy:vm:hypervisor") == "QEMU"

    def test_cloud_insertion_as_cyclonedx(self):
        """Test inserting a cloud service into the XBOM as CycloneDX format."""
        bom = CyclonedxXbom()
        component = Cloud(
            description="Test Cloud Instance",
            name="kubernetes",
            type="lambda"
        ).as_cyclonedx()
        bom.add(component)

        assert component is not None
        assert len(bom.bom.services) == 1  # type: ignore
        assert bom.bom.services[0].name == "kubernetes"  # type: ignore
    
    def test_cloud_insertion_as_cloud(self):
        """Test inserting a Cloud Instance component into the XBOM."""
        bom = CyclonedxXbom()
        cloud = Cloud(
            description="Test Cloud Instance",
            id="cloud-123",
            name="kubernetes",
            type="lambda"
        )
        bom.add(cloud)
        assert cloud is not None
        assert len(bom.bom.services) == 1  # type: ignore
        service = list(bom.bom.services)[0]  # type: ignore
        assert service.name == "kubernetes"
        assert service.description == "Test Cloud Instance"
        
        # Validate provider information
        assert service.provider is not None
        assert service.provider.name == "kubernetes"
        
        # Validate all properties are set correctly
        assert service.properties is not None
        properties_dict = {prop.name: prop.value for prop in service.properties}
        assert properties_dict.get("otupy:type") == "cloud"
        assert properties_dict.get("otupy:cloud:type") == "lambda"
        assert properties_dict.get("otupy:cloud:id") == "cloud-123"
    
    def test_host_insertion_as_cyclonedx(self):
        """Test inserting a host component into the XBOM as CycloneDX format."""
        bom = CyclonedxXbom()
        component = Host(
            id="test-id",
            name=Hostname("hostname"),
        ).as_cyclonedx()
        bom.add(component)

        assert component is not None
        assert len(bom.bom.components) == 1  # type: ignore
        assert bom.bom.components[0].name == "hostname"  # type: ignore
        assert bom.bom.components[0].type == ComponentType.PLATFORM  # type: ignore
        assert bom.bom.components[0].properties is not None  # type: ignore
        properties_dict = {prop.name: prop.value for prop in bom.bom.components[0].properties}  # type: ignore
        assert properties_dict.get("otupy:host:id") == "test-id"

    def test_host_insertion_as_host(self):
        """Test inserting a Host component into the XBOM."""
        bom = CyclonedxXbom()
        host = Host(
            id="test-id",
            name=Hostname("hostname"),
        )
        bom.add(host)

        assert host is not None
        assert len(bom.bom.components) == 1  # type: ignore
        assert bom.bom.components[0].name == "hostname"  # type: ignore
        assert bom.bom.components[0].type == ComponentType.PLATFORM  # type: ignore
        assert bom.bom.components[0].properties is not None  # type: ignore
        properties_dict = {prop.name: prop.value for prop in bom.bom.components[0].properties}  # type: ignore
        assert properties_dict.get("otupy:host:id") == "test-id"

    def test_container_insertion_as_cyclonedx(self):
        """Test inserting a container component into the XBOM as CycloneDX format."""
        bom = CyclonedxXbom()
        # Container only takes namespace, status, and image - no name/id/description
        component = Container(
            namespace="default",
            status="running",
            image="test-image"
        ).as_cyclonedx()
        bom.add(component)

        assert component is not None
        assert len(bom.bom.components) == 1  # type: ignore
        assert bom.bom.components[0].type == ComponentType.CONTAINER  # type: ignore

    def test_container_insertion_as_container(self):
        """Test inserting a Container component into the XBOM."""
        bom = CyclonedxXbom()
        container = Container(
            namespace="default",
            status="running",
            image="test-image"
        )
        bom.add(container)

        assert container is not None
        assert len(bom.bom.components) == 1  # type: ignore
        component = list(bom.bom.components)[0]  # type: ignore
        assert component.type == ComponentType.CONTAINER
        
        # Validate all properties are set correctly
        assert component.properties is not None
        properties_dict = {prop.name: prop.value for prop in component.properties}
        assert properties_dict.get("otupy:type") == "container"
        assert properties_dict.get("otupy:container:namespace") == "default"
        assert properties_dict.get("otupy:container:status") == "running"
        assert properties_dict.get("otupy:container:image") == "test-image"

    def test_iot_insertion_as_cyclonedx(self):
        """Test inserting an IOT component into the XBOM as CycloneDX format."""
        bom = CyclonedxXbom()
        # IOT only takes type parameter - no name/description
        component = IOT(
            type="sensor"
        ).as_cyclonedx()
        bom.add(component)

        assert component is not None
        assert len(bom.bom.components) == 1  # type: ignore
        assert bom.bom.components[0].type == ComponentType.DEVICE  # type: ignore

    def test_iot_insertion_as_iot(self):
        """Test inserting an IOT component into the XBOM."""
        bom = CyclonedxXbom()
        iot = IOT(
            type="sensor"
        )
        bom.add(iot)

        assert iot is not None
        assert len(bom.bom.components) == 1  # type: ignore
        component = list(bom.bom.components)[0]  # type: ignore
        assert component.type == ComponentType.DEVICE
        
        # Validate all properties are set correctly
        assert component.properties is not None
        properties_dict = {prop.name: prop.value for prop in component.properties}
        assert properties_dict.get("otupy:type") == "iot"
        assert properties_dict.get("otupy:iot:type") == "sensor"

    def test_network_insertion_as_cyclonedx(self):
        """Test inserting a network service into the XBOM as CycloneDX format."""
        bom = CyclonedxXbom()
        component = Network(
            description="Test Network",
            name="internal-network",
            type=NetworkType("eth")  # Use 'eth' for ethernet as per NetworkType register
        ).as_cyclonedx()
        bom.add(component)

        assert component is not None
        assert len(bom.bom.services) == 1  # type: ignore
        assert bom.bom.services[0].name == "internal-network"  # type: ignore

    def test_network_insertion_as_network(self):
        """Test inserting a Network component into the XBOM."""
        bom = CyclonedxXbom()
        network = Network(
            description="Test Network",
            name="internal-network",
            type=NetworkType("eth")  # Use 'eth' for ethernet
        )
        bom.add(network)

        assert network is not None
        assert len(bom.bom.services) == 1  # type: ignore
        service = list(bom.bom.services)[0]  # type: ignore
        assert service.name == "internal-network"
        assert service.description == "Test Network"
        
        # Validate all properties are set correctly
        assert service.properties is not None
        properties_dict = {prop.name: prop.value for prop in service.properties}
        assert properties_dict.get("otupy:type") == "network"
        # NetworkType should return the type name as registered
        assert properties_dict.get("otupy:network:type") is not None

    def test_os_insertion_as_cyclonedx(self):
        """Test inserting an OS component into the XBOM as CycloneDX format."""
        bom = CyclonedxXbom()
        # OS takes version, family, release, arch - no name
        component = OS(
            version="22.04",
            family="Linux",
            arch="x86_64"
        ).as_cyclonedx()
        bom.add(component)

        assert component is not None
        assert len(bom.bom.components) == 1  # type: ignore
        assert bom.bom.components[0].type == ComponentType.OPERATING_SYSTEM  # type: ignore

    def test_os_insertion_as_os(self):
        """Test inserting an OS component into the XBOM."""
        bom = CyclonedxXbom()
        os_comp = OS(
            version="22.04",
            family="Linux",
            arch="x86_64"
        )
        bom.add(os_comp)

        assert os_comp is not None
        assert len(bom.bom.components) == 1  # type: ignore
        component = list(bom.bom.components)[0]  # type: ignore
        assert component.type == ComponentType.OPERATING_SYSTEM
        
        # Validate all properties are set correctly
        assert component.properties is not None
        properties_dict = {prop.name: prop.value for prop in component.properties}
        assert properties_dict.get("otupy:type") == "os"
        assert properties_dict.get("otupy:os:family") == "Linux"
        assert properties_dict.get("otupy:os:arch") == "x86_64"

    def test_server_insertion_as_cyclonedx(self):
        """Test inserting a server component into the XBOM as CycloneDX format."""
        bom = CyclonedxXbom()
        # Server constructor takes no meaningful parameters currently
        component = Server().as_cyclonedx()
        bom.add(component)

        assert component is not None
        assert len(bom.bom.components) == 1  # type: ignore
        assert bom.bom.components[0].type == ComponentType.PLATFORM  # type: ignore

    def test_server_insertion_as_server(self):
        """Test inserting a Server component into the XBOM."""
        bom = CyclonedxXbom()
        server = Server()
        bom.add(server)

        assert server is not None
        assert len(bom.bom.components) == 1  # type: ignore
        component = list(bom.bom.components)[0]  # type: ignore
        assert component.type == ComponentType.PLATFORM
        
        # Validate all properties are set correctly
        assert component.properties is not None
        properties_dict = {prop.name: prop.value for prop in component.properties}
        assert properties_dict.get("otupy:type") == "server"
        
        # Validate BOM reference is set
        assert component.bom_ref is not None

    def test_web_service_insertion_as_cyclonedx(self):
        """Test inserting a web service into the XBOM as CycloneDX format."""
        bom = CyclonedxXbom()
        component = WebService(
            description="Test Web Service",
            server=Server(),
            port=443,
            endpoint="/api/v1",
            owner="admin"
        ).as_cyclonedx()
        bom.add(component)

        assert component is not None
        assert len(bom.bom.services) == 1  # type: ignore
        assert bom.bom.services[0].name == "web-service"  # type: ignore

    def test_web_service_insertion_as_web_service(self):
        """Test inserting a WebService component into the XBOM."""
        bom = CyclonedxXbom()
        webservice = WebService(
            description="Test Web Service",
            server=Server(),
            port=443,
            endpoint="/api/v1",
            owner="admin"
        )
        bom.add(webservice)

        assert webservice is not None
        assert len(bom.bom.services) == 1  # type: ignore
        service = list(bom.bom.services)[0]  # type: ignore
        assert service.name == "web-service"
        assert service.description == "Test Web Service"
        
        # Validate endpoints
        assert service.endpoints is not None
        assert len(service.endpoints) == 1
        assert str(service.endpoints[0]) == "/api/v1"
        
        # Validate properties are set correctly
        assert service.properties is not None
        properties_dict = {prop.name: prop.value for prop in service.properties}
        assert properties_dict.get("otupy:type") == "web_service"
        assert properties_dict.get("otupy:webservice:port") == "443"
        assert properties_dict.get("otupy:webservice:owner") == "admin"

    def test_pod_insertion_as_cyclonedx(self):
        """Test inserting a pod component into the XBOM as CycloneDX format."""
        bom = CyclonedxXbom()
        # Pod only takes namespace parameter
        component = Pod(
            namespace="default"
        ).as_cyclonedx()
        bom.add(component)

        assert component is not None
        assert len(bom.bom.components) == 1  # type: ignore
        assert bom.bom.components[0].type == ComponentType.PLATFORM  # type: ignore

    def test_pod_insertion_as_pod(self):
        """Test inserting a Pod component into the XBOM."""
        bom = CyclonedxXbom()
        pod = Pod(
            namespace="default"
        )
        bom.add(pod)

        assert pod is not None
        assert len(bom.bom.components) == 1  # type: ignore
        component = list(bom.bom.components)[0]  # type: ignore
        assert component.type == ComponentType.PLATFORM
        
        # Validate properties are set correctly
        assert component.properties is not None
        properties_dict = {prop.name: prop.value for prop in component.properties}
        assert properties_dict.get("otupy:type") == "pod"
        assert properties_dict.get("otupy:pod:namespace") == "default"
        
        # Validate BOM reference is set
        assert component.bom_ref is not None
