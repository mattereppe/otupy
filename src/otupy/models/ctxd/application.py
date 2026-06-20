from otupy.models.ctxd.ctxd_object import CTXDObject

class Application(CTXDObject):
	""" Application

		Software application: this should bind to a SBOM.
	"""
	version: str = None
	""" version of the application """
	owner: str = None
	""" owner of the application """
	app_type: str = None
	""" type of the application """

	def __init__(self, app=None, description = None, id = None, name = None, version = None, owner = None, app_type = None):
		if isinstance(app, Application):
			super().__init__(name=app.name, description=app.description, id=app.id)
			self.version = app.version
			self.owner = app.owner
			self.app_type = app.app_type
		else:	
			super().__init__(name=name, description=description, id=id)
			self.version = version 
			self.owner = owner 
			self.app_type = app_type 


	def get_subtype(self):
		""" Might be replace in the future with a subtype type """
		return self.app_type

	def __repr__(self):
		return (f"Application({super().__repr__()},"
	             f"version='{self.version}', owner={self.owner}, app_type='{self.app_type}')")
	
	def __str__(self):
		return self.__repr__()
