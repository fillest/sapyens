import contextlib
import urllib
import urllib2
import urlparse
import json
import logging
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden, HTTPUnprocessableEntity
from pyramid.response import Response
import pyramid.security
from pyramid.settings import asbool


log = logging.getLogger(__name__)


class LogoutView (object):
	route_name = 'logout'
	route_path = '/logout'
	permission = None
	redirect_route = None

	@classmethod
	def include_to_config (cls, config):
		config.add_route(cls.route_name, cls.route_path)
		config.add_view(cls(), route_name = cls.route_name, permission = cls.permission)

	def __call__ (self, context, request):
		url = self._make_redirect_url(request)
		response = HTTPFound(location = url)
		return self._update_response(response, request)

	def _make_redirect_url (self, request):
		if self.redirect_route:
			return request.route_url(self.redirect_route)
		else:
			return request.application_url

	def _update_response (self, response, request):
		response.headerlist.extend(pyramid.security.forget(request))
		return response

class LoginView (object):
	route_name = 'login'
	route_path = '/login'
	permission = pyramid.security.NO_PERMISSION_REQUIRED
	renderer = 'sapyens.views:templates/login.mako'
	base_template = 'sapyens.views:templates/base.mako'
	add_as_forbidden_view = True
	page_title = "Sign in"
	redirect_url_session_key = 'login_redirect_url'
	enable_email_form = True
	enable_services = False

	@classmethod
	def include_to_config (cls, config):
		config.add_route(cls.route_name, cls.route_path)
		view = cls()
		config.add_view(view, route_name = cls.route_name, renderer = cls.renderer, permission = cls.permission)
		if cls.add_as_forbidden_view:
			config.add_forbidden_view(view, renderer = cls.renderer)

	def __call__ (self, context, request):
		data = self._process_input(context, request)
		if self.redirect_url_session_key not in request.session:
			request.session[self.redirect_url_session_key] = data['redirect_url']
			#TODO remember if it was POST? save data?

		#TODO of not self.enable_email_form
		auth_failed = False
		if request.method == 'POST':
			if self._verify_credentials(data, request):
				del request.session[self.redirect_url_session_key]

				response = HTTPFound(location = data['redirect_url'])
				return self.update_response(response, request, data)
			else:
				auth_failed = True

		if isinstance(context, HTTPForbidden):
			# RFC on 401: "The response MUST include a WWW-Authenticate header field"
			# RFC on 403: "Authorization will not help and the request SHOULD NOT be repeated."
			# So 403 seems to be the less broken choice (everybody already do this in the wild anyway)
			request.response.status = 403

		template_vars = {
			'auth_failed': auth_failed,
			'data': data,
			'base_template': self.base_template,
			'page_title': self.page_title,
			'enable_email_form': self.enable_email_form,
			'enable_services': self.enable_services,
		}
		if self.enable_services:
			template_vars['service_redirect_urls'] = {'google': request.route_path(GoogleSignInRedirectView.route_name)}
		return template_vars

	def _process_input (self, context, request):
		return {
			'redirect_url': self._process_redirect_url(context, request),
			#TODO use wtform
			'userid': request.POST.get('userid', '').strip(),
			'password': request.POST.get('password', '').strip(),
		}

	def _get_default_redirect_url (self, request):
		return request.application_url

	def _process_redirect_url (self, context, request):
		url = request.session.get(self.redirect_url_session_key)
		if isinstance(context, HTTPForbidden):
			if not request.POST.get('_login_submit'):
				#user hit protected url
				#can't just check method == POST because the original hit could be POST
				#TODO (or this view invocation is always GET first? check) 
				url = request.url
				request.session[self.redirect_url_session_key] = url #TODO move this out somehow

			#else user submitted form

			#TODO this is buggy
			#   File "/opt/logmill/venv/local/lib/python2.7/site-packages/gunicorn/workers/sync.py", line 134, in handle_request
			#     respiter = self.wsgi(environ, resp.start_response)
			#   File "/opt/logmill/venv/local/lib/python2.7/site-packages/pyramid/router.py", line 242, in __call__
			#     response = self.invoke_subrequest(request, use_tweens=True)
			#   File "/opt/logmill/venv/local/lib/python2.7/site-packages/pyramid/router.py", line 217, in invoke_subrequest
			#     response = handle_request(request)
			#   File "/opt/logmill/venv/local/lib/python2.7/site-packages/pyramid/tweens.py", line 46, in excview_tween
			#     response = view_callable(exc, request)
			#   File "/opt/logmill/venv/local/lib/python2.7/site-packages/pyramid/config/views.py", line 355, in rendered_view
			#     result = view(context, request)
			#   File "/opt/logmill/venv/local/lib/python2.7/site-packages/sapyens/views/__init__.py", line 63, in __call__
			#     data = self._process_input(context, request)
			#   File "/opt/logmill/venv/local/lib/python2.7/site-packages/sapyens/views/__init__.py", line 99, in _process_input
			#     'redirect_url': self._process_redirect_url(context, request),
			#   File "/opt/logmill/venv/local/lib/python2.7/site-packages/sapyens/views/__init__.py", line 119, in _process_redirect_url
			#     assert url.startswith(request.application_url), url #TODO
			# AttributeError: 'NoneType' object has no attribute 'startswith'
			url = url or ''
			# assert url.startswith(request.application_url), url #TODO
		else:
			if not url:
				#user clicked "sign in", so use page he came from
				url = request.referer  #TODO can be relative? check
			#else user submitted form
			assert url.startswith(request.application_url), url #TODO

		if not url.startswith(request.application_url):
			url = self._get_default_redirect_url(request)
		
		return url

	def _verify_credentials (self, data, request):
		if 'auth.password' in request.registry.settings:
			return data['password'] == request.registry.settings['auth.password']
		else:
			log.warning("auth.password not defined in settings")
			return False

	@classmethod
	def update_response (cls, response, request, data):
		response.headerlist.extend(pyramid.security.remember(request, data['userid']))
		return response


# class FacebookRedirectView (object):
# 	def __init__ (self, app_id, make_redirect_uri, scope = 'email'):
# 		self.app_id = app_id
# 		self.make_redirect_uri = make_redirect_uri #TODO better naming
# 		self.scope = scope

# 	def __call__ (self, context, request):
# 		#https://developers.facebook.com/docs/reference/dialogs/oauth/
# 		#https://developers.facebook.com/docs/howtos/login/server-side-login/
# 		params = dict(
# 			client_id = self.app_id,
# 			redirect_uri = self.make_redirect_uri(request),
# 			state = self._make_state(request),
# 		)
# 		if self.scope:
# 			params['scope'] = self.scope
# 		url = 'https://www.facebook.com/dialog/oauth/?' + urllib.urlencode(params)
# 		return HTTPFound(location = url)

# 	def _make_state (self, request):
# 		return 'test'

# class FacebookCallbackView (object):
# 	def __init__ (self, app_id, make_redirect_uri, app_secret, json_loads = json.loads):
# 		self.app_id = app_id
# 		self.make_redirect_uri = make_redirect_uri
# 		self.app_secret = app_secret
# 		self.json_loads = json_loads

# 	def _read_url (self, url):
# 		with contextlib.closing(urllib2.urlopen(url)) as resp:
# 			return resp.read()

# 	def _on_finish (self, request, data):
# 		pass

# 	def __call__ (self, context, request):
# 		assert request.GET['state'] == 'test' #TODO

# 		params = dict(
# 			client_id = self.app_id,
# 			redirect_uri = self.make_redirect_uri(request),
# 			client_secret = self.app_secret,
# 			code = request.GET['code'],
# 		)
# 		# fb_host = 'localhost'
# 		fb_host = 'graph.facebook.com'
# 		url = 'https://' + fb_host + '/oauth/access_token?' + urllib.urlencode(params)
		
# 		resp = self._read_url(url)
# 		resp = urlparse.parse_qs(resp)
# 		[access_token] = resp['access_token']
# 		# [expires] = resp['expires']

# 		params = dict(
# 			access_token = access_token,
# 		)
# 		url = 'https://' + fb_host + '/me?' + urllib.urlencode(params)
# 		resp = self._read_url(url)
# 		resp = self.json_loads(resp)
# 		#TODO
# 		# print resp
# 		assert 'error' not in resp
# 		assert 'id' in resp

# 		self._on_finish(request, resp)

# 		#TODO
# 		return HTTPFound(location = '/')






#TODO reworked copypaste
class GoogleRedirectView (object):
	"""see https://developers.google.com/accounts/docs/OAuth2WebServer"""

	route_name = None  #abstract
	route_path = None  #abstract
	permission = pyramid.security.NO_PERMISSION_REQUIRED
	callback_route = None  #abstract

	@classmethod
	def include_to_config (cls, config):
		config.add_route(cls.route_name, cls.route_path)
		config.add_view(cls(config.registry.settings), route_name = cls.route_name, permission = cls.permission)

	def __init__ (self, settings):
		assert self.callback_route
		self.app_id = settings.get('services.google.app_id')
		self.scope = settings.get('services.google.scope', 'https://www.googleapis.com/auth/userinfo.email')
		self.approval_prompt = settings.get('services.google.scope', 'auto')

	def __call__ (self, context, request):
		params = dict(
			response_type = 'code',
			client_id = self.app_id,
			redirect_uri = self._make_callback_url(request),
			state = self._make_state(request),
			approval_prompt = self.approval_prompt,
		)
		if self.scope:
			params['scope'] = self.scope
		url = 'https://accounts.google.com/o/oauth2/auth?' + urllib.urlencode(params)
		return HTTPFound(location = url)

	def _make_state (self, request):
		return request.session.get_csrf_token()

	def _make_callback_url (self, request):
		return request.route_url(self.callback_route)

class GoogleRegisterRedirectView (GoogleRedirectView):
	route_name = 'service.google.redirect.register'
	route_path = route_name
	callback_route = 'service.google.callback.register'

class GoogleSignInRedirectView (GoogleRedirectView):
	route_name = 'service.google.redirect.sign_in'
	route_path = route_name
	callback_route = 'service.google.callback.sign_in'

class GoogleCallbackView (object):
	route_name = None  #abstract
	route_path = None  #abstract
	permission = pyramid.security.NO_PERMISSION_REQUIRED
	json_loads = staticmethod(json.loads)
	callback_route = None  #abstract
	user_model_class = None  #abstract

	@classmethod
	def include_to_config (cls, config):
		config.add_route(cls.route_name, cls.route_path)
		config.add_view(cls(config.registry.settings), route_name = cls.route_name, permission = cls.permission)

	def __init__ (self, settings):
		self.app_id = settings.get('services.google.app_id')
		self.scope = settings.get('services.google.scope', 'https://www.googleapis.com/auth/userinfo.email')
		self.app_secret = settings.get('services.google.app_secret')	

	def __call__ (self, context, request):
		if not self._check_state(request.GET['state'], request):
			#TODO friendlier message
			raise HTTPUnprocessableEntity()

		error = request.GET.get('error')
		if error == 'access_denied':
			#TODO
			return HTTPFound(location = request.application_url)

		access_token = self._fetch_access_token(request)

		user_info = self._fetch_user_info(access_token)
		#TODO checks
		# print user_info
		assert 'error' not in user_info
		assert 'id' in user_info, user_info
		assert 'email' in user_info, user_info
		assert user_info['verified_email'], user_info

		res = self._on_success(request, user_info)
		if isinstance(res, Response):
			return res
		else:
			return self._remember_and_redirect(request, user_info, res)

	def _remember_and_redirect (self, request, user_info, res):
		url = request.session.pop(LoginView.redirect_url_session_key, None)
		resp = HTTPFound(location = url or request.application_url)
		return LoginView.update_response(resp, request, {'userid': user_info['email']})

	def _fetch_access_token (self, request):
		params = dict(
			client_id = self.app_id,
			redirect_uri = self._make_callback_url(request),
			client_secret = self.app_secret,
			code = request.GET['code'],
			grant_type = 'authorization_code',
		)
		host = 'accounts.google.com'
		url = 'https://%s/o/oauth2/token' % host
		
		try:
			resp = self._fetch_url(url, params)
		except Exception as e:
			log.debug(e.read())
			raise
		
		resp = self.json_loads(resp)
		return resp['access_token']

	def _make_callback_url (self, request):
		return request.route_url(self.callback_route)

	def _fetch_user_info (self, access_token):
		params = dict(
			access_token = access_token,
		)
		url = 'https://www.googleapis.com/oauth2/v1/userinfo?' + urllib.urlencode(params)
		resp = self._fetch_url(url)
		return self.json_loads(resp)

	def _fetch_url (self, url, params = None):
		#TODO handle errors
		with contextlib.closing(urllib2.urlopen(url, urllib.urlencode(params) if params else None)) as resp:
			return resp.read()

	def _on_success (self, request, user_info):
		user = self.user_model_class.query.filter_by(email = user_info['email']).first()
		if user:
			if not user.is_enabled:
				#TODO show message
				raise NotImplementedError("user #%s is disabled" % user.id)
			elif user.auth_type != 'google':
				#TODO show message and suggest linking
				raise NotImplementedError("%s != google" % user.auth_type)
		else:
			if asbool(request.registry.settings.get('sign_in.services.register_nonexistent', True)):
				#TODO kinda copypaste from registration
				user = self.user_model_class(
					email = user_info['email'],
					password = '',
					group = 'normal', #TODO make default and customizable
					auth_type = 'google',
				).add()
			else:
				return Response(body = 'Registration is disabled', content_type = 'text/plain')

		return user

	def _check_state (self, value, request):
		return value == self._get_real_state(request)

	def _get_real_state (self, request):
		return request.session.get_csrf_token()

# class GoogleRegisterCallbackView (GoogleCallbackView):
# 	route_name = GoogleRegisterRedirectView.callback_route
# 	route_path = route_name

class GoogleSignInCallbackView (GoogleCallbackView):
	route_name = GoogleSignInRedirectView.callback_route
	route_path = route_name
	callback_route = GoogleSignInRedirectView.callback_route

	# def _on_success (self, request, user_info):
	# 	if not self._verify_credentials(user_info, request):
	# 		#TODO show message or register
	# 		raise HTTPFound(location = request.application_url)

	# def _verify_credentials (self, data, request):
	# 	return data['email'] == request.registry.settings['auth.google.email']