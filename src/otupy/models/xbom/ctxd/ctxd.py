from otupy import Map, ArrayOf, URI

from otupy.models.ctxd import Service, Link
from otupy.models.xbom.ctxd.service_data import ServiceData
from otupy.models.xbom.ctxd.link_data import LinkData

class Ctxd(Map):
	""" Ctxd object

		The Ctxd object implements the JSON schema provided at:
		https://github.com/mattereppe/otupy/blob/discovery/schemas/json/ctxd/ctxd-v2.0.json
	"""
	fieldtypes = {'creator': str, 'jsonschema': URI, 'date': int, 'services': ArrayOf(ServiceData), 'links': ArrayOf(LinkData) }

