# -*- coding: utf-8 -*-
from tc import TeamCityRESTApiClient
import json

from datetime import datetime, timedelta
import time
import sys
import urllib2
import traceback
import base64


def set_color(bridge, color, light_ids=None):
    light_ids = list(map(int, light_ids)) # Convert string array to int array (values of light id's are nummeric)
    lights = bridge.get_light_objects()
    for light in lights:
        if light_ids and light.light_id not in light_ids:
            continue
        light.on = True;
        light.brightness = color["bri"]
        light.hue = color["hue"]
        light.saturation = color["sat"]
        light.effect = color["effect"]

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

def print_status(msg):
    print(time.strftime("%H:%M:%S") + ': ' + msg)

def update_build_lamps(tc_login, config, bridge):
    
    tc = create_team_city_client(tc_login)
    all_projects = tc.get_all_projects().get_from_server()
    
    with open('projects.txt', 'w') as file_handler:
        for p in all_projects[u'project']:
            file_handler.write("%s\n" % p[u'id'])
    
    for watch_project in config[u'teamcity'][u'watch']:
        running = False
        failed_build = False
        ok_projects = []
        for p in all_projects[u'project']:
            project_id = p[u'id']

            if project_id in watch_project[u'projectid']:
                project = tc.get_project_by_project_id(project_id).get_from_server()
                statuses = []
                for build_type in project[u'buildTypes'][u'buildType']:
                    #print "now checking ", build_type[u'id']
                    # Get build status for specified build type id
                    b = tc.get_all_builds().set_build_type(build_type[u'id']).set_lookup_limit(2).set_branch("default:any").set_running(False).get_from_server()
                    if u'build' in b:
                        status = b[u'build'][0][u'status']
                        statuses.append(status)
                    ok_projects.append(not 'FAILURE' in statuses)

                    # Getting current running builds for specified build type id
                    r = tc.get_all_builds().set_build_type(build_type[u'id']).set_lookup_limit(2).set_running(True).get_from_server()
                    if u'build' in r:
                        print_status(r[u'build'][0][u'buildTypeId'] + " RUNNING" )
                        running = r[u'build'][0][u'running']
                    elif u'build' in b:
                        print_status(b[u'build'][0][u'buildTypeId'] + " " + str(status))
                    else:
                        print_status("No builds found!")
    
        color_key = u'success' if all(ok_projects) else u'fail'
        if running:
            color_key = u'running'
        if (u'fail' in color_key):
            failed_build = True;

        set_color(bridge, config[u'colors'][color_key], watch_project[u'light_ids'].keys())
    
    #if(failed_build):
    #    import subprocess
    #    subprocess.call(['omxplayer', 'alert.mp3'])


def update_lamps(tc_login, config, now, bridge_creator):    
    bridge = bridge_creator(config[u'bridge'])

    bridge.connect()
    full_config = bridge.get_api()

    today18 = now.replace(hour=18, minute=0, second=0, microsecond=0)
    today06 = now.replace(hour=6, minute=0, second=0, microsecond=0)

    if now > today06 and now < today18:
        print_status("Connected to bridge "+ full_config["config"]["ipaddress"] + " with bridge id: " + full_config["config"]["bridgeid"])
        update_build_lamps(tc_login, config, bridge)
    else:
        off(bridge)


def _create_bridge(bridge_config):
    from phue import Bridge
    host = bridge_config[u'host']
        
    return Bridge(host)


def main():
    tc_login_path = '{}/{}'.format(sys.path[0], 'tc_login.json')
    config_path = '{}/{}'.format(sys.path[0], 'config.json')
    with open(config_path) as config_file:    
        config = json.load(config_file)
    with open(tc_login_path) as tc_login_file:
        tc_login = json.load(tc_login_file)
    update_lamps(tc_login, config, datetime.now(), _create_bridge)


if __name__ == "__main__":
    main()
    #try:
        
    #except Exception as e:
#        print_status(e.message);
#        raise(e)
