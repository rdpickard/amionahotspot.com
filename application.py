import flask
import os
import json
import requests
import ipaddress

import redis

application = flask.Flask(__name__)
application.config['TEMPLATES_AUTO_RELOAD'] = True

ip2location_api_base_url = "https://api.ip2location.com/v2/?ip={query_ip}&key={api_key}&package=WS24"


@application.route('/')
def index():
    """
    Renders the 'index' page
    :return:
    """

    ok_response_json = {
        "amionahotspot": False,
        "amionahotspot_numeric": -1,
        "network_guess": "-",
        "geo_location_guess": "-",
        "isp_guess": "-",
        "netspeed_guess": "-",
        "from_cache": False
    }

    ip2location_api_key = os.environ.get("ip2location_api_key")

    if ip2location_api_key is None:
        response = application.response_class(
            response=json.dumps({"error": "No ip2location API Key set"}),
            status=500,
            mimetype='application/json'
        )
        return response

    redis_connection = None
    if os.environ.get("REDIS_URL", None) is not None:
        redis_connection = redis.from_url(os.environ.get("REDIS_URL"))

    # Get the IP of the HTTP requester host. This could have gone through proxies/load balancers so look for a
    # X-Forwarded-For header. Will return a http 500 failure to the requester if the IP is non-routable
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

    # If there is a redis instance configured, see if the IP is in there
    if redis_connection is not None:
        cahced_ok_response_json = redis_connection.get(request_ip)
        if cahced_ok_response_json is not None:
            ok_response_json = cahced_ok_response_json
            ok_response_json["from_cache"] = True

    if not ok_response_json["from_cache"]:
        # the default value of "from_cache" is False, so either there is no redis backing or the requested IP wasn't in
        # the redis backing. Fetch teh geoIP data from the ip2location service

        ip2location_response = requests.get(
            ip2location_api_base_url.format(query_ip=request_ip, api_key=ip2location_api_key))

        if ip2location_response.status_code == 200 :
            if ip2location_response.json().get("mobile_brand", "-") != '-':
                ok_response_json["amionahotspot"] = True
                ok_response_json["amionahotspot_numeric"] = 1
                ok_response_json["network_guess"] = ip2location_response.json().get("mobile_brand")
            else:
                ok_response_json["amionahotspot_numeric"] = 0

            ok_response_json["geo_location_guess"] = "{}/{}/{}".format(
                ip2location_response.json().get("country_code", "Country Unavailable"),
                ip2location_response.json().get("region_name", "Region Unavailable"),
                ip2location_response.json().get("city_name", "City Unavailable")
            )
            ok_response_json["isp_guess"] = ip2location_response.json().get("isp", "ISP Unavailable")
            ok_response_json["netspeed_guess"] = ip2location_response.json().get("net_speed", "Speed Unavailable")

            # If there is a redis instance configured, add the geoIP data to it for 1 day's time
            if redis_connection is not None:
                redis_connection.set(request_ip, ok_response_json, ex=86400)

        else:
            # Else if the the ip2location query didn't return a 200
            response = application.response_class(
                response=json.dumps({"error": "Response status code from ip2location is {}. Expecting 200".format(
                    ip2location_response.status_code)}),
                status=500,
                mimetype='application/json'
            )
            return response

        response = application.response_class(
            response=json.dumps(ok_response_json),
            status=200,
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
