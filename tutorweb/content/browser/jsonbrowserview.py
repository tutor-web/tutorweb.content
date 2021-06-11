import json
import logging

from AccessControl import Unauthorized
from App.config import getConfiguration
from zope.publisher.interfaces import NotFound
from zExceptions import Redirect, BadRequest

from Products.Five.browser import BrowserView


class JSONBrowserView(BrowserView):
    def asDict(self, data):
        """Return dict to be turned into JSON"""
        raise NotImplementedError

    def json_format(self, o):
        if self.request.form.get('pprint', None) is not None:
            return json.dumps(o, indent=4)
        return json.dumps(o)

    def __call__(self):
        try:
            # Is there a request body?
            if self.request.get_header('content_length') > 0:
                # NB: Should be checking self.request.getHeader('Content-Type') ==
                # 'application/json' but zope.testbrowser cannae do that.
                self.request.stdin.seek(0)
                data = json.loads(self.request.stdin.read())
            else:
                data = None

            out = self.asDict(data)
            self.request.response.setStatus(200)
            self.request.response.setHeader("Content-type", "application/json")
            return self.json_format(out)
        except Unauthorized, ex:
            self.request.response.setStatus(403)
            self.request.response.setHeader("Content-type", "application/json")
            return self.json_format(dict(
                error=ex.__class__.__name__,
                message=str(ex),
            ))
        except Redirect, ex:
            # Return as Unauthorized, so Javascript can redirect full page
            self.request.response.setStatus(403)
            self.request.response.setHeader("Content-type", "application/json")
            return self.json_format(dict(
                error=ex.__class__.__name__,
                location=str(ex),
            ))
        except NotFound, ex:
            self.request.response.setStatus(404)
            self.request.response.setHeader("Content-type", "application/json")
            return self.json_format(dict(
                error=ex.__class__.__name__,
                message=str(ex),
            ))
        except BadRequest, ex:
            self.request.response.setStatus(400)
            self.request.response.setHeader("Content-type", "application/json")
            return self.json_format(dict(
                error=ex.__class__.__name__,
                message=str(ex),
            ))
        except Exception, ex:
            if getConfiguration().debug_mode:
                import traceback
            logging.error("Failed call: " + self.request['URL'])
            logging.exception(ex)
            self.request.response.setStatus(500)
            self.request.response.setHeader("Content-type", "application/json")
            return self.json_format(dict(
                error=ex.__class__.__name__,
                message=str(ex),
                stacktrace=traceback.format_exc() if getConfiguration().debug_mode else '',
            ))
