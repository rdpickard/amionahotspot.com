import json
import sys
from urllib2 import Request, urlopen


def run(test_config):
    """
    Entry function for nGenius Pulse Custom Test running on an nPulse agent.

    Makes HTTPS request to amionahotspot web service. Returns request results to Pulse Server.

    :param str test_config: Serialized ``test_config`` dictionary as a JSON formatted stream
    :return: Serialized ``results`` dictionary as a JSON formatted stream
    :rtype: str
    """

    # Convert the test_config JSON string into a python dictionary for easy use
    config = json.loads(test_config)

    try:

        request = Request("https://amionahotspot.herokuapp.com/")

        response = urlopen(request)

        res_body = response.read()

        return res_body

    except urllib.error.HTTPError as e:
        return None

