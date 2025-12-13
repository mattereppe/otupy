from otupy import Record, ArrayOf
from otupy.profiles.ctxd.data.os import OS
from otupy.profiles.ctxd.data.application import Application
from otupy.types.data.hostname import Hostname

class Computer(Record):
	""" Computer
   	
	  The Computer model abstract the bundle of an operating system and application software. It may be hosted on a physical 
		server or virtual machine.	  
	"""
	description: str = None
	""" Generic description of the Computing environment """
	id: str = None
	""" ID of the computer """
	hostname: Hostname = None
	""" Hostname of the computer"""
	os: OS = None
	""" Operating System of the computer """
	apps: ArrayOf(Application) = None
	""" List of applications installed on this computer """

	def __init__(self, description:str = None, id:str = None, hostname:Hostname = None, os:OS = None, apps: ArrayOf(Application)=None):
		if(isinstance(description, Computer)):
			self.description = description.description
			self.id = description.id
			self.apps = description.apps
			self.hostname = description.hostname
			self.os = description.os
		else:
			self.description = description if description is not None else None
			self.apps = apps if apps is not None else None
			self.id = id if id is not None else None
			self.hostname = hostname if hostname is not None else None
			self.os = os if os is not None else None
		self.validate_fields()

	def __repr__(self):
		return (f"Computer(description='{self.description}', id={self.id}, "
	             f"hostname='{self.hostname}', os={self.os})")
	
	def __str__(self):
		return f"Computer(" \
	            f"description={self.description}, " \
	            f"id={self.id}, " \
	            f"hostname={self.hostname}, " \
	            f"os={self.os})"

	def validate_fields(self):
		if self.description is not None and not (isinstance(self.description, str) or isinstance(self.description, Computer)):
			raise TypeError(f"Expected 'description' to be of type str, but got {type(self.description)}")
		if self.apps is not None and not isinstance(self.id, ArrayOf(Application)):
			raise TypeError(f"Expected 'id' to be of type str, but got {type(self.id)}")
		if self.hostname is not None and not isinstance(self.hostname, Hostname):
			raise TypeError(f"Expected 'hostname' to be of type Hostname, but got {type(self.hostname)}")
		if self.os is not None and not isinstance(self.os, OS):
			raise TypeError(f"Expected 'os' to be of type {OS}, but got {type(self.os)}")
