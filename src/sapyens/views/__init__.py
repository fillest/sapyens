import contextlib
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden, HTTPUnprocessableEntity
import pyramid.security
import operator
import urllib
import urllib2
import urlparse
import json


class LogoutView (object):
	def __init__ (self, redirect_route = None):
		self._redirect_route = redirect_route

	def __call__ (self, request):
		#TODO csrf?
		response = HTTPFound(location = self._make_redirect_url(request))
		return self._updated_response(response, request)

	def _make_redirect_url (self, request):
		if self._redirect_route:
			return request.route_url(self._redirect_route)
		else:
			return request.application_url

	def _updated_response (self, response, request):
		response.headerlist.extend(pyramid.security.forget(request))
		return response

class LoginView (object):
	route_name = 'login'
	route_path = '/login'
	permission = pyramid.security.NO_PERMISSION_REQUIRED
	renderer = 'sapyens.views:templates/login.mako'
	base_template = 'sapyens.views:templates/base.mako'
	add_as_forbidden_view = True
	page_title = "Log in"

	def __init__ (self, context, request):
		self.request = request
		self.context = context

	@classmethod
	def include_to_config (cls, config):
		config.add_route(cls.route_name, cls.route_path)
		config.add_view(cls, route_name = cls.route_name, renderer = cls.renderer, permission = cls.permission)

		if cls.add_as_forbidden_view:
			config.add_forbidden_view(cls, renderer = cls.renderer)

	def __call__ (self):
		#TODO csrf
		data = self._parse_input()

		auth_failed = False

		if self.request.method.upper() == 'POST':
			if self._verify_credentials(data):
				response = HTTPFound(location = data['redirect_url'])
				return self._updated_response(response, data)
			else:
				auth_failed = True

		return {
			'auth_failed': auth_failed,
			'data': data,
			'base_template': self.base_template,
			'page_title': self.page_title,
		}

	def _parse_input (self):
		return {
			'userid': self.request.POST.get('userid', ''),
			'password': self.request.POST.get('password', ''),
			'redirect_url': self._decide_redirect_url(),
		}

	def _get_default_redirect_url (self, request):
		return self.request.application_url

	def _decide_redirect_url (self):
		redirect_url = self.request.POST.get('redirect_url')

		if not redirect_url:
			if isinstance(self.context, HTTPForbidden):
				redirect_url = self.request.url
			else:
				redirect_url = self._get_default_redirect_url(self.request)
				# redirect_url = request.referer  #TODO can be relative?
				# if not redirect_url:
				# 	redirect_url = request.url
				# 	#TODO custom route? + natural /login hit

		if not redirect_url.startswith(self.request.application_url):
			redirect_url = self._get_default_redirect_url(self.request)
		
		return redirect_url

	def _verify_credentials (self, data):
		return data['password'] == self.request.registry.settings.get('auth.password')

	def _updated_response (self, response, data):
		response.headerlist.extend(pyramid.security.remember(self.request, data['userid']))
		return response

class FacebookRedirectView (object):
	def __init__ (self, app_id, make_redirect_uri, scope = 'email'):
		self.app_id = app_id
		self.make_redirect_uri = make_redirect_uri #TODO better naming
		self.scope = scope

	def __call__ (self, context, request):
		#https://developers.facebook.com/docs/reference/dialogs/oauth/
		#https://developers.facebook.com/docs/howtos/login/server-side-login/
		params = dict(
			client_id = self.app_id,
			redirect_uri = self.make_redirect_uri(request),
			state = self._make_state(request),
		)
		if self.scope:
			params['scope'] = self.scope
		url = 'https://www.facebook.com/dialog/oauth/?' + urllib.urlencode(params)
		return HTTPFound(location = url)

	def _make_state (self, request):
		return 'test'

class FacebookCallbackView (object):
	def __init__ (self, app_id, make_redirect_uri, app_secret, json_loads = json.loads):
		self.app_id = app_id
		self.make_redirect_uri = make_redirect_uri
		self.app_secret = app_secret
		self.json_loads = json_loads

	def _read_url (self, url):
		with contextlib.closing(urllib2.urlopen(url)) as resp:
			return resp.read()

	def _on_finish (self, request, data):
		pass

	def __call__ (self, context, request):
		assert request.GET['state'] == 'test' #TODO

		params = dict(
			client_id = self.app_id,
			redirect_uri = self.make_redirect_uri(request),
			client_secret = self.app_secret,
			code = request.GET['code'],
		)
		# fb_host = 'localhost'
		fb_host = 'graph.facebook.com'
		url = 'https://' + fb_host + '/oauth/access_token?' + urllib.urlencode(params)
		
		resp = self._read_url(url)
		resp = urlparse.parse_qs(resp)
		[access_token] = resp['access_token']
		# [expires] = resp['expires']

		params = dict(
			access_token = access_token,
		)
		url = 'https://' + fb_host + '/me?' + urllib.urlencode(params)
		resp = self._read_url(url)
		resp = self.json_loads(resp)
		#TODO
		# print resp
		assert 'error' not in resp
		assert 'id' in resp

		self._on_finish(request, resp)

		#TODO
		return HTTPFound(location = '/')