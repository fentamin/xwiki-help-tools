import sys
import os
import argparse
import httplib
import json
import urllib
import codecs

def build_page_rest_url(path, wiki, parent, title):
    result = path + "/rest/wikis/" + wiki
    for p in parent.split("."):
        result += "/spaces/" + p
    result += "/pages/" + title
    return urllib.quote(result)

def prepare_header(username, password):
    return {
        "Authorization" : "Basic " + urllib.base64.encodestring(username+":"+password).strip()    
    }

parser = argparse.ArgumentParser()
parser.add_argument("--url", "-U", dest = "url", nargs = "?", default = os.getenv('XWIKI_URL'), help = "base url of your xwiki, http://192.168.0.1:8080/xwiki e.g.; you also can use XWIKI_URL system variable to specify")
parser.add_argument("--username", "-u", dest = "username", nargs = "?", default = os.getenv('XWIKI_USER'), help = "XWIKI username, system variable - XWIKI_USER ")
parser.add_argument("--password", "-p", dest = "password", nargs = "?", default = os.getenv('XWIKI_PWD'), help = "XWIKI password, system variable XWIKI_PWD ")
parser.add_argument("--parent", "-P", dest = "parent", nargs = "?", help = "point separated path to your page home, XWiki.New Pages e.g.")
parser.add_argument("--title", "-c", dest = "title", nargs = "?", help = "your page title")
parser.add_argument("--wiki", "-W", dest = "wiki", nargs = "?", default = "xwiki", help = "if you use non-default wiki home you can specify other, default : xwiki")
parser.add_argument("--content", "-C", dest ="content", nargs = "?", type = argparse.FileType("rb"), default = sys.stdin, help = "file with your page content, will be readed from STDIN if not specified")
parser.add_argument("--attachments", "-a", dest = "attachments", nargs="*", type = argparse.FileType("rb"), help = "files will be attached to your page")

args = parser.parse_args(sys.argv[1:])
content = args.content.read()

# Prepare http headers
headers = prepare_header(args.username, args.password)
headers.update({ 
    "Content-type": "application/x-www-form-urlencoded; charset=utf-8"
})

params = urllib.urlencode({
    "title": args.title,
    "parent": args.parent + ".WebHome",
    "content": content
})

baseurl = httplib.urlsplit(args.url)
resturl = build_page_rest_url( baseurl.path, args.wiki, args.parent, args.title)

connection = httplib.HTTPConnection(baseurl.hostname, baseurl.port)
connection.request('PUT', resturl, params, headers)
resp = connection.getresponse()
connection.close()

ok = (resp.status == httplib.ACCEPTED) | ( resp.status == httplib.CREATED )

if ok:
    print "Page :", args.title, ", Status:", resp.reason
else:
    print "Page creation filed.", resp.reason
    sys.exit(-1)

if ok & ( args.attachments != None ):
    if len(args.attachments) > 0 :
        for f in args.attachments:
            headers = prepare_header(args.username, args.password)
            headers.update({
                "ContentType": "application/octet-stream"
            })
            connection = httplib.HTTPConnection(baseurl.hostname, baseurl.port)
            connection.request('PUT', resturl + "/attachments/" +  f.name, f, headers)
            resp = connection.getresponse()
            connection.close()
            print "Attachment :", f.name, ", Status :", resp.reason
