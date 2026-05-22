import copy
import logging

from otupy import Encoders, ArrayOf, DateTime

from otupy.models.ctxd import Service, Link, Consumer
from otupy.models.xbom.xbom import Xbom
from otupy.profiles.xbom import XbomFormat, XbomEncoding
from otupy.models.xbom.ctxd.ctxd import Ctxd
from otupy.models.xbom.ctxd.service_data import ServiceData
from otupy.models.xbom.ctxd.link_data import LinkData

logger = logging.getLogger(__name__)

# TODO: Use miranda official repository
JSONSCHEMA="https://github.com/mattereppe/otupy/blob/discovery/schemas/json/ctxd/ctxd-v2.0.json"

class CtxdXbom(Xbom):
	""" Otupy native Xbom format

		The Ctxd Xbom format is directly mapped to the otupy ctxd data model.
		It makes use of otupy encoding method for serialization. 
		
		The definition of the Ctxd Xbom format is given with a JSON schema:
		https://github.com/mattereppe/otupy/blob/discovery/schemas/json/ctxd/ctxd-v2.0.json
	"""

	format = XbomFormat.ctxd

	def create(self, services: ArrayOf(Service) = [], links: ArrayOf(Link) = [], consumer: Consumer=None) -> any:
		""" Create the Xbom

			Creates a Ctxd Xbom from the list of Services and Links.
			discards a previously created Xbom.

			:param services: A list of otupy ``Service``.
			:param links: A list of otupy ``Link``.
			:param consumer: The actuator that is generating this Xbom.
			:return: Return the Xbom created.
		"""
		self.xbom = Ctxd()
		self.xbom['services'] = ArrayOf(ServiceData)()
		self.xbom['links'] = ArrayOf(LinkData)()
		for s in services:
			self.xbom['services'].append(ServiceData(service=copy.deepcopy(s), consumer=copy.deepcopy(consumer)))
		for l in links:
			self.xbom['links'].append(LinkData(link=l, consumer=consumer))
		
		self.xbom['date'] = DateTime()
		try:
			self.xbom['creator'] = consumer.actuator['asset_id'] + "@" + str(consumer.host)
		except:
			self.xbom['creator'] = "unkwnon"
		self.xbom['jsonschema'] = JSONSCHEMA

		return self.xbom


	def serialize(self, encoding: XbomEncoding) -> str:
		""" Serialize the Xbom

			Serializes the Xbom in the provided encoding scheme.
			If no Xbom has been previously generated, should return an empty string.

			:param encoding: The serialization scheme to be used. 
			:return: A string containing the encoded Xbom.
		"""
		if self.xbom:
			encoder = Encoders[encoding.name].value
			return encoder.encode(self.xbom)
		else:
			return ""


	def deserialize(self, xbom: str, encoding: XbomEncoding) -> any:
		""" Deserialize a Xbom

			Deserialises a Xbom, stores it internally and returns the Xbom in its
			format, using the class registered in otupy for that format. 
			Any Xbom previously created, loaded, or deserialized is dropped.

			:param xbom: The encoded Xbom.
			:param encoding: The serialization method used to encode the provided Xbom.
			:return: The Xbom in its native format.
		"""
		encoder = Encoders[encoding.name].value
		self.xbom = encoder.decode(xbom, Ctxd)
		return self.xbom

	def summary(self) -> str:
		""" A summary of the ctxd content, mostly for Debug purposes """
		res = ""
		try:
			tot_services = 0
			tot_links = 0
			for item in self.xbom.get('services', []):
				sub=""
				if item.service.subservices is not None:
					for s in item.service.subservices:
						sub+=str(s)+","
				res = res + f"Service: {item.service.sid} [{item.service.name}] {{sub}}\n"
				tot_services = tot_services+1
			for item in self.xbom.get('links', []):
				peers=""
				if item.link.peers is not None:
					for p in item.link.peers:
						peers+=str(p.sid)+"@"+str(p.consumer)+" ["+str(p.role)+"], "
				res = res + f"Link: {item.link.sid} [{item.link.role}] -- ({item.link.link_type}) --> {peers}\n"
				tot_links = tot_links+1
			res = res + f"Found {tot_services} service(s), {tot_links} link(s)"
		except Exception as e:
			logger.error("Unable to summarize bom content: %s", e)
			res = "No service/link found!"
		return res

