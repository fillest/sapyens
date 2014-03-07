from zope.interface import implementer
from pyramid.interfaces import ISession
from pyramid.compat import PY3
import base64
import os
import calendar
import datetime


def _manage_accessed(wrapped):
    def accessed(session, *arg, **kw):
    	print wrapped
        # session.accessed = int(time.time())
        # if not session._dirty:
        #     session._dirty = True
        #     def set_cookie_callback(request, response):
        #         session._set_cookie(response)
        #         session.request = None # explicitly break cycle for gc
        #     session.request.add_response_callback(set_cookie_callback)
        return wrapped(session, *arg, **kw)
    return accessed

def make_session_factory (cookie_name = 's', manage_accessed = _manage_accessed, base_class = dict):
	@implementer(ISession)
	class SessionFactory (base_class):
		session_model = None

		def __init__ (self, request):
			

			self.request = request

			sess_id = request.cookies.get(cookie_name)
			state = self._fetch_state(sess_id, request)
			if state:
				pass

				self.new = False  #interface
			else:
				state = {}
				self.new = True  #interface
				self.created = calendar.timegm(datetime.utcnow().utctimetuple())  #interface
			
			super(SessionFactory, self).__init__(state)

		def _fetch_state (self, sess_id, request):
			# raise NotImplementedError("Abstract method")
			self.session_model.query

		get = manage_accessed(dict.get)
		__getitem__ = manage_accessed(dict.__getitem__)
		items = manage_accessed(dict.items)
		values = manage_accessed(dict.values)
		keys = manage_accessed(dict.keys)
		__contains__ = manage_accessed(dict.__contains__)
		__len__ = manage_accessed(dict.__len__)
		__iter__ = manage_accessed(dict.__iter__)
		iteritems = manage_accessed(dict.iteritems)
		itervalues = manage_accessed(dict.itervalues)
		iterkeys = manage_accessed(dict.iterkeys)
		has_key = manage_accessed(dict.has_key)
		clear = manage_accessed(dict.clear)
		update = manage_accessed(dict.update)
		setdefault = manage_accessed(dict.setdefault)
		pop = manage_accessed(dict.pop)
		popitem = manage_accessed(dict.popitem)
		__setitem__ = manage_accessed(dict.__setitem__)
		__delitem__ = manage_accessed(dict.__delitem__)
		#TODO check if all methods covered

		def changed (self):
			"""Mark the session as changed. A user of a session should call this method after he or she mutates a mutable object that is a value of the session"""
			#session is updated each request

		def invalidate (self):
			self.clear()
			#TODO remove cookie/session?

		@manage_accessed
		def flash(self, msg, queue='', allow_duplicate=True):
			storage = self.setdefault('_f_' + queue, [])
			if allow_duplicate or (msg not in storage):
				storage.append(msg)

		@manage_accessed
		def pop_flash(self, queue=''):
			storage = self.pop('_f_' + queue, [])
			return storage

		@manage_accessed
		def peek_flash(self, queue=''):
			storage = self.get('_f_' + queue, [])
			return storage

		@manage_accessed
		def new_csrf_token(self):
			token = base64.urlsafe_b64encode(os.urandom(69))  #number is arbitrary but avoids trailing '='s
			self['_csrft_'] = token
			return token

		@manage_accessed
		def get_csrf_token(self):
			token = self.get('_csrft_', None)
			if token is None:
				token = self.new_csrf_token()
			return token
		
	return SessionFactory