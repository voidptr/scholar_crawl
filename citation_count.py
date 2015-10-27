#! /usr/bin/env python
"""
This module provides classes for querying Google Scholar and parsing
returned results.  It currently *only* processes the first results
page.  It is not a recursive crawler.
"""
# Version: 1.0 -- $Date: 2013-10-09 13:48:12 -0500 (Wed, 9 Oct 2013) $
#
# ChangeLog
# ---------
#
# 1.0:  Initial Revision
#
# Copyright 2013--Rosangela Canino-Koning. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import socks
import socket
def create_connection(address, timeout=None, source_address=None):
    sock = socks.socksocket()
    sock.connect(address)
    return sock
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)
socket.socket = socks.socksocket
socket.create_connection = create_connection
import urllib2

import scholar as sch
import csv
import optparse
import time
import random
import sys

import unicodedata
import subprocess
import levenshtein as ld


## GLOBAL VARIABLES GOVERNING THE TOR STATE
tor = None
tor_started = False

class TorProxy():
    """
    A class providing a singleton TOR proxy.
    """

    def __init__(self, verbose=False):
        self.running = False
        self.process = None
        self.verbose = verbose

    def stop(self):
        if self.verbose:
            print "STOPPING TOR"

        if self.running and self.process != None:
            self.process.terminate();

            while True:
                line = self.process.stdout.readline()
                line = line.strip()
                if line.find("Catching signal TERM, exiting cleanly.") > -1:
                    if self.verbose:
                        print line
                    time.sleep(1)
                    self.running = False
                    return True 
        else:
            if self.verbose:
                print "TOR WAS NOT RUNNING."
            return False

    def start(self):
        if self.verbose:
            print "STARTING TOR"

        if self.running == False:
            self.process = subprocess.Popen("tor", stdout=subprocess.PIPE)

            while True:
                line = self.process.stdout.readline()
                line = line.strip();

                if line.find("Bootstrapped 100%: Done.") > -1:
                    if self.verbose:
                        print line

                    time.sleep(2)
                    self.running = True
                    return True
                if line.find("Could not bind to 127.0.0.1:9050: Address already in use. Is Tor already running?") > -1:
                    if self.verbose:
                        print line
                    return False

        else:
            if self.verbose:
                print "TOR IS ALREADY RUNNING"
            return False
    
    def kill(self):
        if self.verbose:
            print "KILLING OLD TOR PROCESS AND TRYING AGAIN"
        subprocess.Popen(["killall", "tor"]);
        time.sleep(2)
        self.running = False ## it had better be :(
        
    def fetch_ip(self):
        if self.verbose:
            print "FETCHING IP"

        count = 0
        while True:
            try:
                return (True, (urllib2.urlopen("http://www.ifconfig.me/ip").read()))
            except Exception as inst:
                if self.verbose:
                    print inst
                    print "Failed to fetch IP. Trying again."
                count = count + 1
                if count > 5:
                    return (False, '')

    def init(self):
        count = 0
        while True:
            if self.start():
                (success, ip) = self.fetch_ip()
                print "My IP: " + ip
                return True
            count = count + 1
            if count > 5:
                return False

    def restart(self):
        if not self.stop():
            self.kill()

        self.init()
                 

class CitationScraper():
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.TorProxy = TorProxy(verbose)
    
    def init(self):
        self.TorProxy.init()
   
    def scrub(self, string):
        if isinstance(string, str):
            val = self.scrub_depr(string)
            return unicode(val).encode(sys.stdout.encoding, 'replace')

        elif isinstance(string, unicode):
            return unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')
        else:
            raise Exception("Not a string", "Not a string") 

    def scrub_depr(self, string):
        string = string.replace('', '').replace('', '')

        string = string.replace('\xe2\x80\x90','-')
        string = string.replace('\xe2\x80\x91','-')
        string = string.replace('\xe2\x80\x92','-')
        string = string.replace('\xe2\x80\x93','-')
        string = string.replace('\xe2\x80\x94','--')

        string = string.replace('\xe2\x80\x98',"'")
        string = string.replace('\xe2\x80\x99',"'")
        string = string.replace('\xe2\x80\x9a',"'")
        string = string.replace('\xe2\x80\x9b',"'")

        string = string.replace('\xe2\x80\x9c',"\"")
        string = string.replace('\xe2\x80\x9d',"\"")
        string = string.replace('\xe2\x80\x9e',"\"")
        string = string.replace('\xe2\x80\x9f',"\"")

        string = string.replace('\xcb\x86','^')
        string = string.replace('\xc2\xa0',"-")

        string = ' '.join(string.split())

        #try:
        #    unicode(string).encode(sys.stdout.encoding, 'replace')
        #except UnicodeDecodeError as e:
            
            


        return string




    def qry(self, author, title):
        """
        Tries to query Google Scholar through the Tor Proxy, 
        Fetching new IPs until it is successful
        """

        attemptct2 = 0;
        articles = 0;
        while True:
            attemptct = 0;

            while True: ## keep looping until you can get through
                try:
                    querier = sch.ScholarQuerier(author=author, count=0)
                    querier.query(title)
                    break
                except Exception as inst:
                    print inst
                    print "FAILED TO FETCH DATA! RESTARTING TOR FOR NEW IP. Attempt: " + str(attemptct)
                    self.TorProxy.restart()           
                    attemptct = attemptct + 1

                if attemptct > 10:
                    print "GIVING UP."
                    break  

            articles = querier.articles

            if len(articles) > 0:
                break
            else:
                attemptct2 = attemptct2 + 1
                print "EMPTY RESULTS. Something is wrong, so restarting tor. Attempt: " + str(attemptct2)
                self.TorProxy.restart()

            if attemptct2 > 3:
                print "FUUUCK GIVING UP."
                break  

         

        print "ARTICLES FOUND:"
        found = False;


        for art in articles:

            queriedtitlelower = self.scrub(title.lower())
            retreivedtitlelower = self.scrub(art['title'].lower())

            #print queriedtitlelower
            #print dir(queriedtitlelower)
            #print retreivedtitlelower
            #print dir(retreivedtitlelower)


            if queriedtitlelower == retreivedtitlelower:
                print "FOUND IT -- Num Citations " + str(art['num_citations'])
                print art.as_txt()
                print
                return (True, art['num_citations'])            
            else:
                distance = ld.levenshtein(queriedtitlelower, retreivedtitlelower)
                maxdist = (len(queriedtitlelower) * .1)
                if (distance < maxdist):
                    print "LEVENSHTEIN DISTANCE IS LESS THAN 10% (" + str(maxdist) + "): " + str(distance) + " -- Num Citations " + str(art['num_citations'])
                    print art.as_txt()
                    print
                    return (True, art['num_citations'])    
                else:
                    print "NOPE - LD: " + str(distance) + ". Max Dist: " + str(maxdist)
                    print art.as_txt()
                    print

        return (False, 0)

def main():

    usage = """citation_count.py publications.csv output.csv
    A command-line interface to Google Scholar.
    """

    fmt = optparse.IndentedHelpFormatter(max_help_position=50,
                                         width=100)
    parser = optparse.OptionParser(usage=usage, formatter=fmt)
    parser.add_option("--seq", dest="seq", type="int", help = "Start Processing at item # seq")
    options, args = parser.parse_args()

    if len(args) < 2:
        print 'usage: citation_count.py publications.csv output.csv'
        sys.exit(1)

    pubsfile = args[0]
    outputfile = args[1]

    Scraper = CitationScraper(verbose=True)
    Scraper.init()

    with open(pubsfile, 'rb') as csvfile:
        with open(outputfile, 'wb') as output:

            pubs = csv.DictReader(csvfile)
            outs = csv.DictWriter(output, pubs.fieldnames)

            outs.fieldnames.append('Found')
            outs.fieldnames.append('Citations')
            outs.writeheader()

            count = 0
            for row in pubs:
                if count < options.seq:
                    count = count + 1
                    print "."
                    continue

                # clean up the title line
                title = row['Title']
                title = Scraper.scrub(title)

                print
                print str(count) + ". LOOKING FOR:"
                print "   " + row['Author(s)']
                print "   " + title
                print "--------------------------------------------------"

        
                (found, cits) = Scraper.qry(author=row['Author(s)'], title=title)
                if not found:
                    (found, cits) = Scraper.qry(author='', title=title)

                if found:
                    row['Found'] = 'T'
                else:
                    row['Found'] = 'F'
                
                row['Citations'] = cits
                outs.writerow(row)

##                sleeptime = random.randint(0, 10)
##                print "SLEEPING --- " + str(sleeptime)
##                time.sleep(sleeptime);

                count = count + 1

    print "FINISHED DATA FILE"                

if __name__ == "__main__":
    main()



