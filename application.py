import flask
import os
import json
import requests
import ipaddress

application = flask.Flask(__name__)
application.config['TEMPLATES_AUTO_RELOAD'] = True

ip2location_api_base_url = "https://api.ip2location.com/v2/?ip={query_ip}&key={api_key}&package=WS24&addon=continent,country,region,city,geotargeting,country_groupings,time_zone_info"


@application.route('/')
def index():
    """
    Renders the 'index' page
    :return:
    """

    ok_response_json = {
        "amionahotspot": False,
        "amionahotspot_numeric": -1,
        "network_guess": "-"
    }

    ip2location_api_key = os.environ.get("ip2location_api_key")

    if ip2location_api_key is None:
        response = application.response_class(
            response=json.dumps({"error": "No ip2location API Key set"}),
            status=500,
            mimetype='application/json'
        )
        return response

    request_ip = flask.request.remote_addr
    if ipaddress.IPv4Address(request_ip).is_private and flask.request.headers.get('X-Forwarded-For', None) is not None:
        request_ip = flask.request.headers['X-Forwarded-For']
    elif ipaddress.IPv4Address(request_ip).is_private:
        response = application.response_class(
            response=json.dumps({"error": "Can't lookup {} {} IP in private RFC 1918 space".format(
                flask.request.remote_addr, flask.request.headers['X-Forwarded-For'])}),
            status=500,
            mimetype='application/json'
        )
        return response

    ip2location_response = requests.get(
        ip2location_api_base_url.format(query_ip=request_ip, api_key=ip2location_api_key))

    if ip2location_response.status_code == 200 :
        if ip2location_response.json().get("mobile_brand", "-") != '-':
            ok_response_json["amionahotspot"] = True
            ok_response_json["amionahotspot_numeric"] = 1
            ok_response_json["network_guess"] = ip2location_response.json().get("mobile_brand")
        else:
            ok_response_json["amionahotspot_numeric"] = 0

        response = application.response_class(
            response=json.dumps(ok_response_json),
            status=200,
            mimetype='application/json'
        )
        return response

    else:
        response = application.response_class(
            response=json.dumps({"error": "Response status code from ip2location is {}. Expecting 200".format(ip2location_response.status_code)}),
            status=500,
            mimetype='application/json'
        )
        return response


@application.route('/css/<path:path>')
def send_css(path):
    return flask.send_from_directory('staticfiles/css', path)


@application.route('/js/<path:path>')
def send_js(path):
    return flask.send_from_directory('staticfiles/js', path)


@application.route('/fonts/<path:path>')
def send_font(path):
    return flask.send_from_directory('staticfiles/fonts', path)


@application.route('/media/<path:path>')
def send_media(path):
    return flask.send_from_directory('staticfiles/media', path)


@application.before_first_request
def pre_first_request():
    pass


if __name__ == "__main__":
    application.run()
