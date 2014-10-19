#!/usr/bin/env python
import sys
import urllib
import os.path
import ConfigParser
import time
import json 
from pprint import pprint 
import argparse

def process(type, backup):

    config = ConfigParser.ConfigParser()
    if args.cfg:
        configFilename = args.cfg 
    else:
        configFilename = os.path.join(os.path.dirname(sys.argv[0]), "couch.cfg")
    print "Loading config from", configFilename
    
    if not os.path.isfile(configFilename):
        print "ERROR: You need a config file."
        sys.exit(-1)
    
    config.read(configFilename)
    
    host = config.get("CouchPotato", "host")
    port = config.get("CouchPotato", "port")
    apikey = config.get("CouchPotato", "apikey")

    try:
        ssl = int(config.get("CouchPotato", "ssl"))
    except (ConfigParser.NoOptionError, ValueError):
        ssl = 0
   
    try:
        web_root = config.get("CouchPotato", "web_root")
    except ConfigParser.NoOptionError:
        web_root = ""


    if ssl:
        protocol = "https://"
    else:
        protocol = "http://"
    
    if type == "backup":
        url = protocol + host + ":" + port + web_root + "/api/" + apikey + "/" + "movie.list/?status=active"
        print "Opening URL:", url
        try:
            urlObj = urllib.urlopen(url)
        except IOError, e:
            print "Unable to open URL: ", str(e)
            sys.exit(1)
    
        result = json.load(urlObj)
        imdb_list = [ item["info"]["imdb"] for item in result["movies"] if 'info' in item and 'imdb' in item["info"] ]

        f = open(backup, 'w')
        for imdb in imdb_list:
            f.write(imdb +'\n')
        f.close()

    elif type == "restore":
        f = open(backup, 'r')
        imdb_list = [ line.strip() for line in f ]
        f.close()
        baseurl = protocol + host + ":" + port + web_root + "/api/" + apikey + "/" + "movie.add/?identifier="
        for imdb in imdb_list:
            url = baseurl + imdb
            print "Opening URL:", url
            try:
                urlObj = urllib.urlopen(url)
            except IOError, e:
                print "Unable to open URL: ", str(e)
                sys.exit(1)

parser = argparse.ArgumentParser(description='Backup/Restore Couchpotato wanted list',
                                formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--type', metavar='backup/restore', choices=['backup', 'restore'], required=True,
                    help='')
parser.add_argument('file', help='''If backup: The file to save the wanted list to.
If restore: The file to restore from.''')
parser.add_argument('--cfg', metavar='cfg-file', help='Specify an alternative cfg file')
args = parser.parse_args()
process(args.type, args.file)
