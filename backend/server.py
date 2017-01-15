import http.server
import socketserver
import json
import random
from urllib.parse import urlparse
import urllib.request
import threading
import email.utils as eut
import traceback
PORT = 8080
UrltoResource = {}
UrltoLink = {}
Lock = threading.Lock()

def date_comparison(first_date, second_date):
	return_val = 0
	first = eut.parsedate(first_date)
	second = eut.parsedate(second_date)
	if first == None or second == None:
		return 1000
	return_val += (first[0] - second[0]) * 365 * 24 * 60 * 60
	return_val += (first[1] - second[1]) * 30 * 24 * 60 * 60
	return_val += (first[2] - second[2]) * 24 * 60 * 60
	return_val += (first[3] - second[3]) * 60 * 60
	return_val += (first[4] - second[4]) * 60
	return_val += (first[5] - second[5])
	return return_val

def image_mode(urls, resource):
	return_urls = []
	for url in urls:
		if(resource[url]["type"] == "image") and resource[url]["isStatic"]:
			return_urls.append(url)
	return return_urls
def script_mode(urls, resource):
	return_urls = []
	for url in urls:
		if(resource[url]["type"] == "script") and resource[url]["isStatic"]:
			return_urls.append(url)
	return return_urls
def full_mode(urls, resource):
	return_urls = []
	for url in urls:
		if(resource[url]["isStatic"]):
			return_urls.append(url)
	return return_urls
# def priority_mode(resource, mode = full_mode, num_per_domain = 6):
# 	return

def limit_mode(urls, resource, num_per_domain = 6):
	return_urls = []
	num_url = 0
	while num_url < num_per_domain and len(urls) != 0:
		index = random.randint(0, len(urls) - 1)
		if resource[urls[index]]["isStatic"]:
			return_urls.append(urls[index])
		urls.pop(index)
		num_url += 1

	return return_urls

def debug_mode(urls, resource):
	total_num = len(urls)
	script_num = 0
	image_num = 0
	static_num = 0
	for url in urls:
		if resource[url]['type'] == 'script':
			script_num += 1
		elif resource[url]['type'] == 'image':
			image_num += 1
		if resource[url]['isStatic']:
			static_num += 1
	if total_num != 0:
		print ("image precentage:" + str(image_num / float(total_num)))
		print ("script precentage:" + str(script_num / float(total_num)))
		print ("static resource precentage:" + str(static_num / float(total_num)))
	else:
		print ("total num is 0")

def storeResource(load_r, UrltoResource):
	tabUrl = load_r['tabUrl']
	print(tabUrl)
	if tabUrl in UrltoResource:
		for url in UrltoResource[tabUrl]:
			UrltoResource[tabUrl][url]["isStatic"] = False
			UrltoResource[tabUrl][url]["isFirst"] = False
			UrltoResource[tabUrl][url]["isVisit"] = False
	else:
		UrltoResource[tabUrl] = {}
	for requestId in load_r['resources']:
		if load_r['resources'][requestId]['url'] in UrltoResource[tabUrl] and UrltoResource[tabUrl][load_r['resources'][requestId]['url']]["isVisit"]:
			continue
		if load_r['resources'][requestId]['url'] in UrltoResource[tabUrl]:
			UrltoResource[tabUrl][load_r['resources'][requestId]['url']] = load_r['resources'][requestId]
			UrltoResource[tabUrl][load_r['resources'][requestId]['url']]["isVisit"] = True
			UrltoResource[tabUrl][load_r['resources'][requestId]['url']]["isFirst"] = False
			UrltoResource[tabUrl][load_r['resources'][requestId]['url']]["isStatic"] = True
		else:
			UrltoResource[tabUrl][load_r['resources'][requestId]['url']] = load_r['resources'][requestId]
			UrltoResource[tabUrl][load_r['resources'][requestId]['url']]["isVisit"] = True
			UrltoResource[tabUrl][load_r['resources'][requestId]['url']]["isFirst"] = True
			UrltoResource[tabUrl][load_r['resources'][requestId]['url']]["isStatic"] = False
	UrltoResource = deleteNonStaticResource(UrltoResource, tabUrl)
	UrltoResource = deleteNonCacheResource(UrltoResource, tabUrl)
	debug_mode(UrltoResource[tabUrl].keys(), UrltoResource[tabUrl])
	return UrltoResource

def storeLinkHeader(load_r, UrltoLink):
	tabUrl = load_r["tabUrl"]
	UrltoLink[tabUrl] = {}
	UrltoLink[tabUrl]["dns-prefetch_mode"] = formLinkHeader(UrltoResource, tabUrl, full_mode, True)
	UrltoLink[tabUrl]["full_mode"] = formLinkHeader(UrltoResource, tabUrl, full_mode)
	UrltoLink[tabUrl]["limit_mode"] = formLinkHeader(UrltoResource, tabUrl, limit_mode)
	UrltoLink[tabUrl]["image_mode"] = formLinkHeader(UrltoResource, tabUrl, image_mode)
	UrltoLink[tabUrl]["script_mode"] = formLinkHeader(UrltoResource, tabUrl, script_mode)
	return UrltoLink



def deleteNonStaticResource(UrltoResource, tabUrl):
	delete_array = []
	for url in UrltoResource[tabUrl]:
		if UrltoResource[tabUrl][url]["isStatic"] == False and UrltoResource[tabUrl][url]["isFirst"] == False:
			delete_array.append(url)
	for url in delete_array:
		del UrltoResource[tabUrl][url]
	return UrltoResource

def deleteNonCacheResource(UrltoResource, tabUrl):
	delete_array = []
	for url in UrltoResource[tabUrl]:
		if 'Expires' not in UrltoResource[tabUrl][url] or 'Date' not in UrltoResource[tabUrl][url]:
			continue
		if date_comparison(UrltoResource[tabUrl][url]['Expires'], UrltoResource[tabUrl][url]['Date']) < 2:
			delete_array.append(url)
	for url in delete_array:
		del UrltoResource[tabUrl][url]
	return UrltoResource

# Iterate an dictionary resource, the key is the request url.
# Return: doman name sorted by the num of requests, dictionary whose key is the domain.
def getDomains(resources):
	domainToUrl = {}
	for url in resources:
		hostname = urlparse(url).hostname
		if hostname in domainToUrl:
			domainToUrl[hostname].append(url)
		else:
			domainToUrl[hostname] = []
			domainToUrl[hostname].append(url)
	return sorted(domainToUrl, key=lambda k: len(domainToUrl[k]), reverse=True), domainToUrl

def getUrls(domainToUrl, resource, mode_function):
	return_urls = []
	for domain in domainToUrl:
		urls = domainToUrl[domain]
		return_urls += mode_function(urls, resource)
	return return_urls

def formLinkHeader(UrltoResource, tabUrl, mode_function = full_mode, isdns_prefetch = False):
	link = ""

	if tabUrl in UrltoResource:
		domains, domainToUrl = getDomains(UrltoResource[tabUrl])
		# preconnect (include dns-prefetch)
		for hostname in domains:
			link += "<" + hostname + ">; rel=dns-prefetch,"
		if isdns_prefetch:
			return link
		# preload the resources 
		urls = getUrls(domainToUrl, UrltoResource[tabUrl], mode_function)
		for url in urls:
			link += "<" + url + ">; rel=preload,"
		if mode_function == full_mode:
			print ("full_mode preloaded resource:" + str(len(urls)))
		elif mode_function == limit_mode:
			print ("limit_mode preloaded resource:" + str(len(urls)))
	return link

def analyze(load_r):
	Lock.acquire()
	try:
		global UrltoResource
		global UrltoLink
		UrltoResource = storeResource(load_r, UrltoResource)
		UrltoLink = storeLinkHeader(load_r, UrltoLink)
		Lock.release()
	except:
		traceback.print_exc()
		Lock.release()

class Thread(threading.Thread):
    def __init__(self, t, *args):
        threading.Thread.__init__(self, target=t, args=args)
        self.start() 
class MyHandler(http.server.SimpleHTTPRequestHandler):
	def do_HEAD(s):
		s.send_response(200)
		s.send_header("Content-type", "text/html")
		s.end_headers()
	def do_GET(s):
		"""Respond to a GET request."""

		s.send_response(200)
		s.send_header("Content-type", "application/json")
		s.end_headers()
	def do_POST(s):
		"""Respond to a POST request."""
		global UrltoResource
		global UrltoLink
		s.data_string = s.rfile.read(int(s.headers['Content-Length']))
		load_r = json.loads(s.data_string.decode("UTF-8"))
		s.send_response(200)
		s.send_header("Content-type", "application/json")
		# s.send_header("Link", "<https://ss1.bdstatic.com>; rel=preconnect, <https://www.baidu.com>; rel=preload, ")
		if load_r['type'] == 'analyze':
			s.end_headers()
			r = {'result': 'success'}
			r = json.dumps(r)
			s.wfile.write(bytes(r,'UTF-8'))
			Thread(analyze,load_r)
		elif load_r['type'] == 'predict':
			r = {'result': 'success'}
			r = json.dumps(r)
			Lock.acquire()
			if load_r["tabUrl"] in UrltoLink:
				link = UrltoLink[load_r["tabUrl"]][load_r["mode"]]
				s.send_header("Link", link)
			Lock.release()
			s.end_headers()
			s.wfile.write(bytes(r,'UTF-8'))
		elif load_r['type'] == 'delete':
			s.end_headers()
			print (load_r)



httpd = socketserver.TCPServer(("", PORT), MyHandler)

print("serving at port", PORT)
httpd.serve_forever()