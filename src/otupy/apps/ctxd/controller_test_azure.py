#!../.oc2-env/bin/python3
# Example to use the OpenC2 library with Azure actuator
#

import logging
import otupy as oc2

from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
import otupy.profiles.ctxd as ctxd
from otupy.profiles.ctxd.data.name import Name
from otupy.types.base.array_of import ArrayOf
from otupy.actuators.ctxd.ctxd_actuator_azure import CTXDActuator_azure
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Console logger
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(oc2.LogFormatter(datetime=True, name=True))
logger.addHandler(stdout_handler)

def start_consumer_azure():
    logger.info("Creating consumer for Azure")
    actuators = {}
    ip = '127.0.0.1'
    port = 8080
    endpoint = '/.well-known/openc2'
    actuators[(ctxd.Profile.nsid, "azure")] = CTXDActuator_azure(domain= None,
                                                                            asset_id= "azure",
                                                                            hostname = "azure0",
                                                                            ip = ip,
                                                                            port =port,
                                                                            protocol = 6,
                                                                            endpoint =endpoint,
                                                                            transfer = 1,
                                                                            encoding = 1,
                                                                            subscription_id=None
                                                                            )

    
    c = oc2.Consumer("azure_consumer",actuators=actuators,encoder=JSONEncoder(),transfer=HTTPTransfer(
        host = ip, port = port, endpoint =endpoint
    ))

    
    c.run()  




def main():

    #start_consumer_azure()

    logger.info("Creating Producer for Azure")

    # Producer che comunica con l’actuator Azure
    p = oc2.Producer("producer.azure.test", JSONEncoder(), HTTPTransfer("127.0.0.1", 8080))

    # Actuator profile = Azure (asset_id usato dall’actuator)
    pf = ctxd.Specifiers({'asset_id': 'azure'})

    # Argomenti query → vogliamo informazioni complete
    arg = ctxd.Args({'name_only': False})

    # In questo caso chiediamo tutti i servizi/links noti (Azure Resource Manager)
    context = ctxd.Context(
        services=ArrayOf(Name)(), 
        links=ArrayOf(Name)()
    )

    # Creiamo il comando OpenC2 → query
    cmd = oc2.Command(
        action=oc2.Actions.query,
        target=context,
        args=arg,
        actuator=pf
    )

    logger.info("Sending command to Azure actuator: %s", cmd)

    # Invio comando → la risposta dovrebbe contenere i Resource Groups Azure
    resp = p.sendcmd(cmd)
    logger.info("Got response from Azure actuator: %s", resp)


if __name__ == '__main__':
    main()
