"""
    Generates the TCPDump for all the websites. 
    Connects to browser that is already running, navigates to the required page and capture TCPDump
"""

import json
import websocket
import requests
from dom import DOM
import os
import subprocess
import time
from time import sleep
from slugify import slugify
from har import HAR
from page import Page

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



def run(websites):
    iface = 'wlp4s0'
    loss_rate = 2
    netemRemoveRule = "sudo tc qdisc del dev {} root".format(iface)
    netemCommandRoot = 'sudo tc qdisc add dev {} root handle 1: netem loss {}%'.format(iface, loss_rate)
    os.system(netemRemoveRule)
    os.system(netemCommandRoot)
    host = 'localhost'
    port = '9222'
    response = requests.get("http://%s:%s/json" % (host, port))
    tablist = json.loads(response.text)
    wsdurl = tablist[0]['webSocketDebuggerUrl']
    
    print("Hello")
    for site in websites:
        file = "pcap_files/h3/" + slugify(site) + ".pcap"
        tcp_dump_command = "sudo tcpdump -i wlp4s0 -v -w {}".format(file)
        print("TCP Dump command : ", tcp_dump_command)
        tcp_process = subprocess.Popen(tcp_dump_command, stdout=subprocess.PIPE, shell=True)
        client = ChromeRDPWebsocket(wsdurl, site)
        print("Navigating to the Page :", site)
        time.sleep(10)
        tcp_process.kill()
        print("Killing The TCP command")
        # client.navigate_to_page('about:blank')
    

if __name__ == '__main__':
    
    f = open('endpoints.json')
    websites = []

    endpoints = json.load(f)
    for site in endpoints:
        websites.append(endpoints[site]["100KB"])
        websites.append(endpoints[site]["1MB"])
        websites.append(endpoints[site]["5MB"])
        websites.append(endpoints[site]["small"]["url"])
        websites.append(endpoints[site]["medium"]["url"])
        websites.append(endpoints[site]["large"]["url"])
    
    run(websites)