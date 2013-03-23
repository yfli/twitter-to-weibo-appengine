from google.appengine.api import xmpp
import logging
import webapp2

class XMPPHandler(webapp2.RequestHandler):
    def post(self):
        message = xmpp.Message(self.request.POST)
        logging.debug("weibo %s reply:%s",message.sender, message.body)

app = webapp2.WSGIApplication([('/_ah/xmpp/message/chat/', XMPPHandler)], debug=True)

