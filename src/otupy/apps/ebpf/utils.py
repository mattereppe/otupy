from otupy.core.message import Message
from otupy.encoders import json
from otupy.encoders.json import JSONEncoder
import json

import logging
import otupy as oc2



def handle_response(resp):
    """
    Validate OpenC2 response.
    Raises RuntimeError if status is not OK.
    Returns parsed response body.
    """
    logger = logging.getLogger("ebpf_producer")
    logger.setLevel(logging.INFO)
    m = Message()
    m.set(resp)  # wrap the raw response
    data = JSONEncoder().encode(m)

    try:
        parsed_data = oc2.loads(data)
        status = parsed_data['body']['openc2']['response']['status']
        status_text = parsed_data['body']['openc2']['response']['status_text']

    except AttributeError:
        parsed_data = json.loads(data)
        status = parsed_data['body']['openc2']['response']['status']
        status_text = parsed_data['body']['openc2']['response']['status_text']

    if status != 200:
        logger.error("OpenC2 command failed: %s", status_text)
        raise RuntimeError(f"OpenC2 command failed: {status_text}")

    return parsed_data