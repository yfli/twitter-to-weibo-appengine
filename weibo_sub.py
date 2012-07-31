from google.appengine.api import xmpp
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import logging
from testid import my_weibo_bot, my_weibo_bot_verify_code

class XMPPHandler(webapp.RequestHandler):
    def post(self):
        sender = self.request.get('from').split('/')[0]
        if sender == my_weibo_bot:
            logging.debug("my weibo bot :%s subscribed or want to subscribe", sender)
            xmpp.send_presence(sender)
            #xmpp.send_message(my_weibo_bot, my_weibo_bot_verify_code)
        else:
            logging.debug("Not adding contact:%s", sender)

application = webapp.WSGIApplication([('/_ah/xmpp/subscription/subscribe/', XMPPHandler),('/_ah/xmpp/subscription/subscribed/', XMPPHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
