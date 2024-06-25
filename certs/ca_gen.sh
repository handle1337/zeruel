#https://gist.github.com/soarez/9688998


openssl genrsa -out zeruelCA.key 2048

openssl req -new -x509 -days 3650 -key zeruelCA.key -out zeruelCA.crt -subj "/CN=zeruelproxy CA/C=US"


