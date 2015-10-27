import socks                                                         
import urlparse                                                      

SOCKS_HOST = 'localhost'                                             
SOCKS_PORT = 9050                                                    
SOCKS_TYPE = socks.PROXY_TYPE_SOCKS5                                 

url = 'http://www.whatismyip.com/automation/n09230945.asp'           
parsed = urlparse.urlparse(url)                                      


socket = socks.socksocket()                                          
socket.setproxy(SOCKS_TYPE, SOCKS_HOST, SOCKS_PORT)                  
socket.connect((parsed.netloc, 80))                                  
socket.send('''GET %(uri)s HTTP/1.1                                  
host: %(host)s                                                       
connection: close                                                    

''' % dict(                                                          
    uri=parsed.path,                                                 
    host=parsed.netloc,                                              
))                                                                   

print socket.recv(1024)                                              
socket.close()
