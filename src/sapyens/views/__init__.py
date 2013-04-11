from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden, HTTPUnprocessableEntity
import pyramid.security
import operator
import urllib
import urlparse
import json


class LogoutView (object):
	def __init__ (self, redirect_route):
		self._redirect_route = redirect_route

	def __call__ (self, request):
		#TODO csrf?
		response = HTTPFound(location = self._make_redirect_url(request))
		return self._update_response(response, request)

	def _make_redirect_url (self, request):
		return request.route_url(self._redirect_route)

	def _update_response (self, response, request):
		response.headerlist.extend(pyramid.security.forget(request))
		return response

class LoginView (object):
	def __init__ (self, get_real_password, compare_passwords = operator.eq):
		self._get_real_password = get_real_password
		self._compare_passwords = compare_passwords

	def __call__ (self, context, request):
		#TODO csrf?
		redirect_url = self._decide_redirect_url(request, isinstance(context, HTTPForbidden))

		if request.method.upper() == 'POST':
			username, password = self._try_parse_input(request)

			if self._check_password(username, password, request):
				response = HTTPFound(location = redirect_url)
				return self._update_response(response, request, username)
			else:
				auth_failed = True
		else:
			auth_failed = False

			username = ''
			password = ''

		return {
			'auth_failed': auth_failed,
			'redirect_url': redirect_url,
			'username': username,
			'password': password,
		}

	def _decide_redirect_url (self, request, is_on_forbidden):
		redirect_url = request.POST.get('redirect_url')
		if not redirect_url:
			if is_on_forbidden:
				redirect_url = request.url
			else:
				redirect_url = request.referer  #TODO can be not absolute?
				if not redirect_url:
					redirect_url = request.url
					#TODO custom route? + natural /login hit
		if not redirect_url.startswith(request.application_url):
			redirect_url = request.application_url
		return redirect_url

	def _check_password (self, username, password, request):
		return self._compare_passwords(password, self._get_real_password(username, request))

	def _update_response (self, response, request, username):
		response.headerlist.extend(pyramid.security.remember(request, username))
		return response

	def _try_parse_input (self, request):
		username = request.POST.get('username')
		if username is None:
			raise HTTPUnprocessableEntity()
		password = request.POST.get('password')
		if password is None:
			raise HTTPUnprocessableEntity()
		return username, password

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
		return urllib.urlopen(url).read() #TODO close?

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