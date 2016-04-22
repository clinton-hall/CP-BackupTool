#!/usr/bin/env python
import sys
import urllib
import os
import ConfigParser
import json 
import argparse
import time

# Default values that will be used if not found in CFG
default_host = 'localhost'
default_port = 5050
default_ssl = False

def validateConf(config, section, item):
    try:
        # Special check for ssl
        if item == 'ssl':
            try:
                # Specific to CP-backuptool CFG
                return config.getboolean(section, item)
            except:
                # Specific to CP settings.conf
                if config.get(section, "ssl_key"):
                    return True
                else:
                    return False
        else:
            return config.get(section, item)
    except:
        if item == 'host':
            print "No '%s' found in config, using default: '%s'" % (item, default_host)
            return default_host
        elif item == 'port':
            print "No '%s' found in config, using default: '%s'" % (item, default_port)
            return default_port
        elif item == 'api_key':
            raise Exception("No API key found in configfile")

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

def listWanted(baseurl):
    api_call = "movie.list/?status=active"
    url = baseurl + api_call
    result = apiCall(url)
    return result

def process(type, backup = None):
    config = ConfigParser.ConfigParser()
    if args.cfg:
        configFilename = args.cfg 
    else:
        configFilename = os.path.join(os.path.dirname(sys.argv[0]), "couch.cfg")

    print "Loading config from:", configFilename
    with open(configFilename, "r") as conf:
        config.readfp(conf)

    sections = config.sections()
    host = validateConf(config, sections[0], "host")
    port = validateConf(config, sections[0], "port")
    apikey = validateConf(config, sections[0], "api_key")
    ssl = validateConf(config, sections[0], "ssl")
    web_root = validateConf(config, sections[0], "url_base")

    if ssl:
        protocol = "https://"
    else:
        protocol = "http://"
    
    # Add '/' to beginning of web_root if missing
    if web_root and not web_root[0] == '/':
        web_root = '/' + web_root
    # Remove '/' from end of web_root if present
    if web_root and web_root[-1] == '/':
        web_root = web_root[:-1]

    # The base URL
    baseurl = protocol + host + ":" + str(port) + web_root + "/api/" + apikey + "/"
    if type == "backup":
        result = listWanted(baseurl)

        backup_list = []
        # Check if backup is necessary (i.e skip if no movies found)
        if result['total'] > 0:
            for item in result["movies"]:
                if not ("info" in item or "identifiers" in item):
                    continue
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
    elif type == "delete":
        result = listWanted(baseurl)
        if result['total'] > 0:
            print "Deleting wanted movies..."
            for item in result["movies"]:
                print "Deleting movie '%s'" % item["title"]
                api_call = "movie.delete/?delete_from=wanted&id=%s" % item["_id"]
                url = baseurl + api_call
                apiCall(url, verbose = False)
        else:
            print "No wanted movies to delete"

parser = argparse.ArgumentParser(description='Backup/Restore/Delete Couchpotato wanted list',
                                formatter_class=argparse.RawTextHelpFormatter)
# Require this option
parser.add_argument('--type', metavar='backup/restore/delete', choices=['backup', 'restore', 'delete'],
        required=True, help='''backup: Writes the wanted movies to file.
restore: Adds wanted movies from file.
delete: Delete all your wanted movies''')
parser.add_argument('--file', help='', required=False)
parser.add_argument('--cfg', metavar='cfg-file', help='Specify an alternative cfg file')
args = parser.parse_args()
if args.type == 'backup' or args.type == 'restore':
    if not args.file:
        parser.error('You must specify a file when using %s' % args.type)
process(args.type, args.file)
