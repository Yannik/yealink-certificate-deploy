This automates deployment of ssl certificates (e.g. from letsencrypt) to yealink phones.

It can alternatively done through config key `static.server_certificates.url`, but I'm not sure how updating a cert would work in that case. Also, the cert would need to be secured from access from anyone other than the phone on the provisioning server.

Confirmed working phone models:
  - Yealink T46S

Usage:
```
usage: yealink-certificate-deploy.py [-h] [--headless] [--insecure]
                                     [--no-screenshots] [--debug]
                                     host password certfile

positional arguments:
  host              host
  password          yealink phone admin password
  certfile          certfile should contain both cert and key

optional arguments:
  -h, --help        show this help message and exit
  --headless        run headless
  --insecure        ignore invalid ssl cert on phone (useful for first setup)
  --no-screenshots  disable saving screenshots for each step
  --debug           debug output
```
