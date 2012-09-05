from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden
import pyramid.security
import operator


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
			raise HTTPNotFound()
		password = request.POST.get('password')
		if password is None:
			raise HTTPNotFound()
		return username, password
