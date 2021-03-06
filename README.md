

```bash

# Create virtual environment and install deps
virtualenv env
source env/bin/activate
pip install -r requirements.txt

# Run Chrome or Chromium or Headless shell
/Applications/Chromium.app/Contents/MacOS/Chromium --remote-debugging-port=9222  --enable-benchmarking --enable-net-benchmarking

# Run HAR collector. Take websites from endpoints.json
python client.py


```

### Reference Links
#### Headless Chromium
https://chromium.googlesource.com/chromium/src/+/master/headless/README.md  
https://docs.google.com/document/d/11zIkKkLBocofGgoTeeyibB2TZ_k7nR78v7kNelCatUE/edit#  

https://chromium.googlesource.com/chromium/src/+/master/third_party/WebKit/Source/core/inspector/browser_protocol.json  
https://github.com/salvadormrf/python-chrome-har

https://github.com/cyrus-and/chrome-har-capturer 

https://github.com/triplewy/quic-benchmarks 

https://github.com/Shenggan/quic_vs_tcp

https://github.com/arashmolavi/quic

