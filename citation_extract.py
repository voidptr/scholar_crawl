#! /usr/bin/env python
"""
This module provides classes for querying Google Scholar and parsing
returned results.  It currently *only* processes the first results
page.  It is not a recursive crawler.
"""
# Version: 1.0 -- $Date: 2015-10-29 14:33:12 -0500 (Thu, 29 Oct 2015) $
#
# ChangeLog
# ---------
#
# 3.0:  Updated for 2015. Updated the scholar.py library
#
# 2.0:  Updated for 2014
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




import csv
import optparse
import time
import random
import sys

import unicodedata
import subprocess
from pymongo import MongoClient
import pymongo

MONGODB_HOSTNAME = '127.0.0.1'

def main():

    conn = MongoClient(MONGODB_HOSTNAME, 27017)
    db = conn['scholar'] 
    collection = db.papers

    usage = """citation_extract.py publications.csv output.csv
    A command-line interface to Google Scholar.
    """

    fmt = optparse.IndentedHelpFormatter(max_help_position=50,
                                         width=100)
    parser = optparse.OptionParser(usage=usage, formatter=fmt)
    parser.add_option("--seq", dest="seq", type="int", 
        help = "Start Processing at item # seq")

    options, args = parser.parse_args()

    if len(args) < 2:
        print usage
        sys.exit(1)

    pubsfile = args[0]
    outputfile = args[1]

    records = collection.find()
    total_count = collection.find().count()

    print total_count

    with open(pubsfile, 'rb') as csvfile:
        with open(outputfile, 'wb') as output:

            pubs = csv.DictReader(csvfile)
            outs = csv.DictWriter(output, pubs.fieldnames)

            outs.fieldnames.append('Found')
            outs.fieldnames.append('Citations')
            outs.writeheader()

            count = 0
            for row in pubs:

                # clean up the title line
                title = row['Title']
                item = collection.find_one({'title': title})

                print
                if (count != item['index']):
                    print "============ MISMATCH =========="
                else:
                    print
                print str(count) + ". CSV RECORD:"
                print "   " + row['Author(s)']
                print "   " + title
                print
                print str(item['index']) + ". MONGO RECORD:"

                try:    
                    print "   " + item['author']
                except:
                    print "-->" + row['Author(s)']

                try:    
                    print "   " + item['title']
                except:
                    print "-->" + title

                print "   " + str(item['cites'])
                       
                print "--------------------------------------------------"

                cites = item['cites']
        
                if cites > -1:
                    row['Found'] = 'T'
                else:
                    row['Found'] = 'F'
                
                row['Citations'] = cites
                
                outs.writerow(row)    

                count = count + 1



    print "FINISHED DATA FILE"                

if __name__ == "__main__":
    main()



