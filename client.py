"""
client.py - 
    Spawns the chromium browser process, loads the webpages and saves the HAR file - for both HTTP2 and QUIC
"""

from time import sleep
import simplejson as json
import websocket
import requests
from har import HAR
from page import Page
from dom import DOM
from runtime import Runtime
from slugify import slugify
import os
import subprocess
import time
import shutil
import json



class ChromeRDPWebsocket(object):
    command_id = 0

    def __init__(self, wsurl, target_url):
        self.debugging_url = wsurl
        self.page = None
        self.target_url = target_url

        # websocket.enableTrace(True)

        self.ws = websocket.WebSocketApp(self.debugging_url,\
                                        on_message = self.on_message,\
                                        on_error = self.on_error,\
                                        on_close = self.on_close)
        self.ws.on_open = self.on_open
        self.ws.run_forever() # start running this socket.

    def load_url(self, url):
        # pass
        # var page = new Page(index, url, chrome, options.fetchContent);
        index = 0
        self.page = Page(index, url, self.ws, fetch_content=True)

        # print "## HERE", url
        self.navigate_to_page(url)

    def on_message(self, ws, message):
        '''
        Handle each message.
        '''
        message_obj = json.loads(message)
        # print "## Got message", message_obj

        if self.page:
            self.page.process_message(message_obj)
            if self.page.finished:
                self.close_connection()

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
       print('Socket for {0} is closed.'.format(self.debugging_url))

    def on_open(self, ws):
        self.navigate_to_page('about:blank')
        self.enable_network_tracking()
        self.enable_page_tracking()
        #self.enable_runtime()
        #self.enable_dom()
        self.clear_cache()

        # if self.user_agent is not None:
        #     navigation_utils.set_user_agent(self.ws, self.user_agent)

        # if self.screen_size_config is not None:
        #     navigation_utils.set_device_screen_size(self.ws, self.screen_size_config, self.device_configuration['page_id'])

        self.enable_trace_collection()
        # print 'navigating to url: ' + str(self.url)
        # if self.should_reload:
        #     navigation_utils.reload_page(self.ws)
        # else:
        #     navigation_utils.navigate_to_page(self.ws, self.url)

        # self.load_url('https://www.doubleclickbygoogle.com/articles/mobile-speed-matters/')
        self.load_url(self.target_url)

    def close_connection(self):
        self.ws.close()
        print('Connection closed')

    def clear_cache(self):
        self.enqueue_command(method='Network.clearBrowserCache')
        print('Cleared browser cache')

    def can_clear_cache(self):
        self.enqueue_command(method='Network.canClearBrowserCache')
        print('Cleared browser cache')

    def disable_network_tracking(self):
        self.enqueue_command(method='Network.disable')
        print('Disable network tracking.')

    def disable_page_tracking(self):
        self.enqueue_command(method='Page.disable')
        print('Disable page tracking.')

    def enable_network_tracking(self):
        self.enqueue_command(method='Network.enable')
        print('Enabled network tracking.')

        self.enqueue_command(method='Network.setCacheDisabled', params={"cacheDisabled": True})
        print('Disable debugging connection.')

    def enable_page_tracking(self):
        self.enqueue_command(method='Page.enable')
        print('Enabled page tracking.')

    def enable_trace_collection(self):
        self.enqueue_command(method='Tracing.start')
        print('Enabled trace collection')

    def stop_trace_collection(self):
        self.enqueue_command(method='Tracing.end')
        print('Disables trace collection')

    def get_debugging_url(self):
        return self.debugging_url

    def navigate_to_page(self, url):
        self.enqueue_command(method='Page.navigate', params={"url": url})
        print('Navigating to url:', url)

    @property
    def next_command_id(self):
        self.command_id += 1
        return self.command_id

    # Async
    def enqueue_command(self, method, params={}, callback=None):
        msg = {'id': self.next_command_id, 'method': method, 'params': params}
        self.ws.send(json.dumps(msg))
        sleep(0.3)

    # def evaluate(self, expression):
    #     res = self.enqueue_command(method='Runtime.evaluate', params={"expression": expression})
    #     print 'Evaluating expression'
    #     # return res

    # # Not async
    # def call_command(self, method, params={}, callback=None):
    #     msg = {'id': self.next_command_id, 'method': method, 'params': params}
    #     self.ws.send(json.dumps(msg))
    #     return json.loads(self.ws.recv())


def run(loss_rate, latency, bandwidth, dir, i):
    
    # Host and port on which the chromium will be run with debugging enabled
    host = 'localhost'
    port = '9222'
    iface = 'wlp4s0'

    # Netem commands to emulate the Network constraints
    netemRemoveRule = "sudo tc qdisc del dev {} root".format(iface)
    netemCommandRoot = 'sudo tc qdisc add dev {} root handle 1: netem loss {}%'.format(iface, loss_rate)
    netemCommandBandwidth = "sudo tc qdisc add dev {} parent 1: handle 2: tbf rate {}mbit burst 256kbit latency {}ms mtu 1500".format(iface, bandwidth, latency)    

    # Execute Netem Commands
    os.system(netemRemoveRule)
    os.system(netemCommandRoot)
    os.system(netemCommandBandwidth)

    # Config file that contains the list of websites
    f = open('endpoints.json')
    websites = []

    # Read the file and get the websites list
    endpoints = json.load(f)
    for site in endpoints:
        websites.append(endpoints[site]["100KB"])
        websites.append(endpoints[site]["1MB"])
        websites.append(endpoints[site]["5MB"])
        websites.append(endpoints[site]["small"]["url"])
        websites.append(endpoints[site]["medium"]["url"])
        websites.append(endpoints[site]["large"]["url"])


    #Command with QUIC enabled
    CHROME_TYPE_QUIC = "chromium --remote-debugging-port=9222 --incognito  --enable-benchmarking --enable-net-benchmarking --enable-quic --headless"
    
    # QUIC disabled
    CHROME_TYPE = "chromium --remote-debugging-port=9222  --incognito  --enable-benchmarking --enable-net-benchmarking --disable-quic --headless"            

    test_type = CHROME_TYPE_QUIC
    path = dir + "/"
    if i==2:
        test_type = CHROME_TYPE
    
    # Spawn the browser as a subprocess
    browserProcess = subprocess.Popen(test_type, stdout=subprocess.PIPE, shell=True)
    # wait for the chrome window opening
    time.sleep(1)
    
    #  Get the HAR file for each website
    for url in websites :
        try:
            # find websocket endpoint
            response = requests.get("http://%s:%s/json" % (host, port))
            tablist = json.loads(response.text)
            wsdurl = tablist[0]['webSocketDebuggerUrl']

            # Connect to socket and load the website
            client = ChromeRDPWebsocket(wsdurl, url)

            # Save as HAR file
            har = HAR()
            har.from_page(client.page)
            filename = slugify(url)
            f = open(path + filename+'.har', 'w')
            f.write(json.dumps(har.har, indent=4))
            f.close()

        except Exception as e:
            pass
    browserProcess.kill()


if __name__ == '__main__':
    latency_lst = [1, 100]
    loss_rate_lst = [0, 2]
    bw_list = [2, 10, 50]

    f = open("demofile2.txt", "r+")
    lines = f.readlines()
    
    for bw in bw_list:
        for latency in latency_lst:
            for loss in loss_rate_lst:
                for i in [1, 2]:
                    p = "H3"
                    if i == 2:
                        p = "H2"
                    skip = False
                    for line in lines:
                        arr = line.strip().split("-")
                        print(arr)
                        if(arr[0]) == p and int(arr[1]) == latency and int(arr[2]) == loss and int(arr[3]) == bw:
                            skip = True
                    if skip == True:
                        print("Skiping current run p = ", p, " latency = ", latency, " loss = ", loss, " bw = ", bw)
                        continue
                    out_dir =  p + "=" +  "_latency="+ str(latency) + "_loss=" + str(loss) + "_bw=" + str(bw)
                    path = os.getcwd()
                    path = path + "/" + out_dir
                    isdir = os.path.isdir(path)
                    if not isdir:
                        os.makedirs(out_dir)
                    run(loss, latency, bw, out_dir, i)
                    wt = str(p) + "-" + str(latency) + "-" + str(loss) +  "-" +str(bw)
                    f.write(wt+ os.linesep)
    f.close()
