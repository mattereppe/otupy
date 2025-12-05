from otupy.types.base import Choice
from otupy.core.extensions import Register
from otupy.types.data import Hostname, URI
import uuid


class Name(Choice):
    
    register = Register({'uri': URI, 'reverse-dns': Hostname, 'uuid': uuid.UUID, 'local': str})
    #Il tipo Hostname è utilizzabile per reverse-dns

    def __init__(self, name):
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

    def __str__(self):
        return self.getObj()

    def __eq__(self, other):
        if other == None:
            return False
        if( self.getName() != other.getName() ):
            return False
        if( self.getObj() == other.getObj() ):
            return True

        return False

