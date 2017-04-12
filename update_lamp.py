# -*- coding: utf-8 -*-
from tc import TeamCityRESTApiClient
import json

from datetime import datetime, timedelta
from time import mktime, sleep, strptime
import sys
import urllib2
import traceback
import base64


def set_color(bridge, color, light_ids=None):
	lights = bridge.get_light_objects()
	for light in lights:
		if light_ids and light.light_id not in light_ids:
			continue
		light.brightness = color["bri"]
		light.hue = color["hue"]
		light.saturation = color["sat"]


def on(bridge):
	lights = bridge.get_light_objects()
	for light in lights:
			light.on = True


def off(bridge):
	lights = bridge.get_light_objects()
	for light in lights:
		light.on = False


def create_team_city_client(config):
	tc = config[u'teamcity']
	return TeamCityRESTApiClient(
		tc[u'user'], base64.b64decode(tc[u'password']),
		tc[u'host'], int(tc[u'port']))


def update_build_lamps(config, bridge):
	tc = create_team_city_client(config)	
	all_projects = tc.get_all_projects().get_from_server()	
	watched = config[u'teamcity'][u'watch']

	ok_projects = []
	for p in all_projects[u'project']:
		project_id = p[u'id']
		
		if project_id in watched:
			project = tc.get_project_by_project_id(project_id).get_from_server()
			statuses = []
			for build_type in project[u'buildTypes'][u'buildType']:
				b = tc.get_all_builds().set_build_type(build_type[u'id']).set_lookup_limit(2).get_from_server()
				if u'build' in b:
					status = b[u'build'][0][u'status']
					print b[u'build'][0][u'buildTypeId'], status
					statuses.append(status)

				ok_projects.append(not 'FAILURE' in statuses)

	on(bridge)
	color_key = u'success' if all(ok_projects) else u'fail'
	set_color(bridge, config[u'colors'][color_key], config[u'groups'][u'build_lights'][u'ids'])


def update_lamps(config, now, bridge_creator):	
    bridge = bridge_creator(config[u'bridge'])

    bridge.connect()
    full_config = bridge.get_api()
    print "Connected to bridge "+ full_config["config"]["ipaddress"] + " with bridge id: " + full_config["config"]["bridgeid"]

    today20 = now.replace(hour=20, minute=0, second=0, microsecond=0)
    today06 = now.replace(hour=6, minute=0, second=0, microsecond=0)

    if now > today06 and now < today20:	
        update_build_lamps(config, bridge)
    else:
        off(bridge)


def _create_bridge(bridge_config):
	from phue import Bridge
	if u'id' in bridge_config:
		response = urllib2.urlopen("https://www.meethue.com/api/nupnp")
		upnp = json.load(response)
		
		bid = bridge_config[u'id']
		bridges = (x for x in upnp if x[u'id'] == bid) if bid else iter(upnp)
		print(bridges)
		bridge_object = next(bridges)
		host = bridge_object[u'internalipaddress']
	else:
		host = bridge_config[u'host']
		
	return Bridge(host)


def main():
	config_path = '{}/{}'.format(sys.path[0], 'config.json')
	with open(config_path) as config_file:    
		config = json.load(config_file)
	update_lamps(config, datetime.now(), _create_bridge)


if __name__ == "__main__":
    main()
