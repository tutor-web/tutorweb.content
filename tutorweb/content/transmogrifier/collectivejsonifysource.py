import base64
import json
import urllib
import urllib2
import urlparse

from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection

from collective.transmogrifier.utils import openFileReference
from collective.transmogrifier.utils import defaultMatcher

class CollectiveJsonifySource(object):
    """
    Read some JSON from a collective.jsonify site
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.transmogrifier = transmogrifier
        self.key = defaultMatcher(options, 'key', name)

        self.url = urlparse.urlparse(options.get('url', ''))
        if not self.url.scheme:
            raise ValueError("URL parameter is required")
        self.query = dict(path=self.url.path)
        if 'type' in options:
            self.query['Type'] = dict(
                query=options.get('type').split(','),
                operator="or",
            )

    def __iter__(self):
        for path in catalog_query(self.url, self.query):
            yield fetch_item(self.url, path)


def catalog_query(url, query):
    req = urllib2.Request(
        url.scheme + '://' +
        url.netloc + '/' +
        url.path.split('/')[1] +
        "/portal_catalog/get_catalog_results",
        urllib.urlencode(dict(
            catalog_query=base64.b64encode(str(query)),
        )),
    )
    resp = urllib2.urlopen(req)
    return sorted(json.loads(resp.read()))


def fetch_item(url, path):
    req = urllib2.Request(
        url.scheme + '://' +
        url.netloc + '/' +
        path + '/get_item')
    resp = urllib2.urlopen(req)
    return json.loads(resp.read())


def fetch_children(url, path):
    req = urllib2.Request(
        url.scheme + '://' +
        url.netloc + '/' +
        path + '/get_children')
    resp = urllib2.urlopen(req)
    return json.loads(resp.read())
