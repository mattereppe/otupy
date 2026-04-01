from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.profiles.xbom.data.bom_ref import generate_bom_ref
from otupy.types.base.record import Record


class OS(Record):
	"""OS
    Operating System
    
    The Operating System is one common Execution Environment, which
    can execute almost any software. It will have a full set of libraries
    and applications, as well as many subsystems (file systems, etc.).
	"""
	family: str = None
	""" Family of the OS """
	version: str = None
	""" Version of the OS """
	release: str = None
	""" Release number/string """
	arch: str = None
	""" Supported CPU architecture """


	def __init__(self, os = None, version = None, family = None, release=None,  arch = None):
		if os is not None:
			self.family=os.family
			self.version=os.version
			self.release=os.release
			self.arch=os.family
		else:
			self.family = str(family) 
			self.version = str(version) 
			self.release = str(release) 
			self.arch = str(arch)


	def __repr__(self):
		return (f"OS("
	             f"family={self.family}, version={self.version}, release={self.release}, type={self.arch})")
	
	def __str__(self):
		return self.__repr__()

	def as_cyclonedx(self) -> Component:
		"""Convert OS to CycloneDX component format.
		
		Returns:
			Component: CycloneDX Component with type OPERATING_SYSTEM.
		"""
		properties = [
			Property(name="otupy:type", value="os")
		]
		# if self.id is not None:
		# 	properties.append(Property(name="otupy:os:id", value=self.id))
		if self.family is not None:
			properties.append(Property(name="otupy:os:family", value=self.family))
		if self.arch is not None:
			properties.append(Property(name="otupy:os:arch", value=self.arch))
		
		# Include nested components from ExecutionEnvironment
		
		return Component(
			name= "tmp",
			type=ComponentType.OPERATING_SYSTEM,
			bom_ref=generate_bom_ref("os"),
			version=self.version,
			# description=self.description,
			properties=properties
		)
