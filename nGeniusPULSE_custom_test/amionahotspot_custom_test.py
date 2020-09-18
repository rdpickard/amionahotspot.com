import json
import sys
from urllib2 import Request, urlopen

def run(test_config):
    """
    Every scripted test needs to have a function called 'run' with
    a single argument. This argument provides the script with the optionally defined
    test config variables that are defined in the test type editor and then filled in
    on the test editor.

    :param str test_config: Serialized ``test_config`` dictionary as a JSON formatted stream
    :return: Serialized ``results`` dictionary as a JSON formatted stream
    :rtype: str
    :raises Exception: example of raising an exception.
    """

    # Convert the test_config JSON string into a python dictionary for easy use
    config = json.loads(test_config)

    try:

        request = Request("https://amionahotspot.herokuapp.com/")

        response = urlopen(request)

        res_body = response.read()

        return res_body

        """
        amionahotspot_request = urllib.request.Request("https://amionahotspot.herokuapp.com/")
        amionahotspot_response = urllib.request.urlopen(amionahotspot_request)
        response_data = amionahotspot_response.read()
        repsonse_json = json.loads(response_data.decode(amionahotspot_response.info().get_content_charset('utf-8')))
        return json.dumps(repsonse_json)
        """

    except urllib.error.HTTPError as e:
        return None

#print(run("{}"))