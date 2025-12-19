from otupy.types.base import Choice
from otupy.core.extensions import Register
from otupy.types.data import Hostname, URI
import uuid


class Name(Choice):
    """ Service or Link identifier
    
    	The Name class is designed to contain multiple alternative identifiers for a Service. The current options include:

    	- uri: A valid URI. It is normally expected that the URI corresponds to a reachable service, but this is not strictly required by this implementation, as the URI is only used as identifier (not as a locator).
    	- reverse-dns: This field has the same syntax as a DNS name, but in reverse order (e.g., com.apple.service.xyz). It is commonly used by software frameworks that needs unique names for entities, but does not require to locate them with a DNS.
    	- uuid: A UUID of 128 bits following usual formats and structure.
    	- local: A format-free string that might not be unique and has local meaning only (e.g., "host0").
    
    	The current design assumes a single identifier can be given (differently, e.g., from Specifiers). This choice
    	makes simpler comparing two Names to see if they are equal (with multiple identifiers it is not clear how to
    	manage cases where only a subset matches).
    
    """
    
    register = Register({'uri': URI, 'reverse-dns': Hostname, 'uuid': uuid.UUID, 'local': str})

    def __init__(self, name):
        """ Create a Name object
        
           The correct type is automatically inferred from the type of the supplied object. If a plain string is used, the
           "local" type is used.

          :param name: The identifier of the Service or Link.
        """
        if ( isinstance(name, dict) ):
            if len(name) != 1:
               raise ValueError
            for key, value in name.items():
               n=self.getClass(key)(value) 
            name=n
        if(isinstance(name, Name)):
            super().__init__(name.obj)
        elif not((isinstance(name, URI) or isinstance(name, Hostname) or isinstance(name, uuid.UUID) or isinstance(name, str))):
				# Instantiate as 'local' by default
            super().__init__(name.name.obj)
        else:
            super().__init__(name)

    def get(self):
        """ Return the id of the Service/Link
		  
            Return the identifier stored in this class. 

				:return: A reference to the object that contains the id. The original object type is returned (see 'str' to get a plain string).
        """
        return self.getObj()

    def type(self):
        """ Return the identifier type

			  Return the class of the identifier.

			  :return: The class object of the identifier instance.
        """
        return self.getClass()

    def str(self):
        """ Return the id as plain string

			  Return the id of the Service/Link as plain string, independently of its type.
			  :return: String representation of the object.
        """
        return str(self.getObj())

    def __str__(self):
        """ Return the internal object

			  This method assumes the conversion to string is managed by the object type.
        """
        return self.getObj()

    def __eq__(self, other):
        """ Compare two Names

           The comparison checks both the object type and its value. Two Names who contains the same string but for different 
			  object types (e.g., 'local' and 'uuid' are not considered to be the same).

			  :param other: The Name to compare.
			  :return: True if type and content match.
        """
        if other == None:
            return False
        if( self.getName() != other.getName() ):
            return False
        if( self.getObj() == other.getObj() ):
            return True

        return False

