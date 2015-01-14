#!/usr/bin/env python
import sys
import urllib
import os
import ConfigParser
import json 
import argparse
import time

# Validate mandatory values
def validateConf(config, section, confFile):
    default_host = 'localhost'
    default_port = 5050
    default_ssl = "off"
    config_list = config.items(section)
    for item in config_list:
        # Check host value in cfg
        if item[0] == 'host' and not item[1]:
            print "No value found for '%s' in cfg %s" % (item[0], confFile)
            print "Writing default value '%s' in cfg %s"  % (default_host, confFile)
            config.set(section, item[0], default_host)
            writeConf(config, confFile)

        # Check port value in cfg
        if item[0] == 'port' and not item[1]:
            print "No value found for '%s' in cfg %s" % (item[0], confFile)
            print "Writing default value '%s' in cfg %s"  % (default_port, confFile)
            config.set(section, item[0], str(default_port))
            writeConf(config, confFile)

        # Check apikey value in cfg
        if item[0] == 'apikey' and not item[1]:
            raise ValueError("'%s' can't be empty in cfg %s" % (item[0], confFile))

        # Check ssl value in cfg
        if item[0] == 'ssl' and not item[1]:
            print "No value found for '%s' in cfg %s" % (item[0], confFile)
            print "Writing default value '%s' in cfg %s"  % (default_ssl, confFile)
            config.set(section, item[0], str(default_ssl))
            writeConf(config, confFile)

def writeConf(config, confFile):
    with open(confFile, "w") as conf:
        config.write(conf)
    conf.close()

def apiCall(url, verbose = True):
    if verbose:
        print "Opening URL:", url
    try:
        urlObj = urllib.urlopen(url)
    except:
        print "Failed to open URL:", url
        print "Caught following:"
        raise

    result = json.load(urlObj)
    if result:
        return result
    else:
        return None

def process(type, backup):
    config = ConfigParser.ConfigParser()
    if args.cfg:
        configFilename = args.cfg 
    else:
        configFilename = os.path.join(os.path.dirname(sys.argv[0]), "couch.cfg")

    print "Loading config from:", configFilename
    with open(configFilename, "r") as conf:
        config.readfp(conf)

    # Validate config
    validateConf(config, "CouchPotato", configFilename)

    host = config.get("CouchPotato", "host")
    # Must be an INT
    port = config.getint("CouchPotato", "port")
    apikey = config.get("CouchPotato", "apikey")
    # Must be a boolean ("1", "yes", "true", "on", "0", "no" "false" and "off" are supported)
    ssl = config.getboolean("CouchPotato", "ssl")
    web_root = config.get("CouchPotato", "web_root")

    if ssl:
        protocol = "https://"
    else:
        protocol = "http://"
    
    # The base URL
    baseurl = protocol + host + ":" + str(port) + web_root + "/api/" + apikey + "/"
    if type == "backup":
        api_call = "movie.list/?status=active"
        url = baseurl + api_call
        result = apiCall(url)
        backup_list = []
        # Check if backup is necessary (i.e skip if no movies found)
        if result['total'] > 0:
            for item in result["movies"]:
                movie_list = []
                try:
                    # Try the current data structure
                    movie_list.append(item["identifiers"]["imdb"])
                except:
                    # Use old data structure for backward compatibility
                    movie_list.append(item["info"]["imdb"])

                # If the profile ID is found (optional)
                if item["profile_id"]:
                    movie_list.append(item["profile_id"])
                # Append the movie list to backup list
                backup_list.append(movie_list)

            print "found %s wanted movies, writing file..." % len(backup_list)
            with open(backup, 'w') as f:
                json.dump(backup_list, f)
            f.close()
            print "Backup file completed:", backup
        else:
            print "No wanted movies found"

    elif type == "restore":
        # Do a managed search prior to restoring
        print "Doing a full managed scan..."
        api_call = "manage.update/?full=1"
        url = baseurl + api_call
        result = apiCall(url)

        # Check progress
        api_call = "manage.progress"
        url = baseurl + api_call
        result = apiCall(url)
        while result['progress'] != False:
            result = apiCall(url, verbose=False)
            time.sleep(1)
        print "Managed scan completed"

        with open(backup, 'r') as f:
            movie_list = json.load(f)
        f.close()

        for movie in movie_list:
            # Add movies along with profile id (if not found or empty; default will be used)
            if len(movie) == 1:
                movie.append("")
            api_call = "movie.add/?identifier=%s&profile_id=%s" %(movie[0], movie[1])
            url = baseurl + api_call
            result = apiCall(url)

parser = argparse.ArgumentParser(description='Backup/Restore Couchpotato wanted list',
                                formatter_class=argparse.RawTextHelpFormatter)
# Require this option
parser.add_argument('--type', metavar='backup/restore', choices=['backup', 'restore'],
                    required=True, help='')
parser.add_argument('file', help='''If backup: The file to save the wanted list to.
If restore: The file to restore from.''')
parser.add_argument('--cfg', metavar='cfg-file', help='Specify an alternative cfg file')
args = parser.parse_args()
process(args.type, args.file)
