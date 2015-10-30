Query Google Scholar with TOR and Python
----------------------------------------

Requires: 
---------

Tor
MongoDB
SocksiPy

To run, in separate consoles:

% while true; do ./multitor.sh; python multi_citation_count.py test.csv; done
% while true; do sleep 240; killall tor; killall python; done

To extract the output:

% python citation_extract.py test.csv out.csv
