openssl genrsa -out zeruelCA.key 2048
#browser
openssl req -new -x509 -days 3650 -key zeruelCA.key -out zeruelCA.crt -subj "/CN=zeruelproxy CA"

#self.connection = ssl.wrap_socket(self.connection, keyfile=self.certkey, certfile=certpath, server_side=True)
openssl genrsa -out cert.key 2048
