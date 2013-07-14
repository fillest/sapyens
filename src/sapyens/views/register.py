import contextlib
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden, HTTPUnprocessableEntity
import pyramid.security
import urllib
import urllib2
import urlparse
import json
import wtforms.validators as v
import wtforms as w
import base64
import os
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.renderers import render
import datetime
import sapyens.views


class RegForm (w.Form):
	email = w.TextField("Email", [v.DataRequired(), v.Length(min = 2), v.Email()])
	password = w.PasswordField("Password", [v.DataRequired(), v.Length(min = 4)])

class RegisterView (object):
	route_name = 'register'
	route_path = '/register'
	renderer = 'sapyens.views:templates/register/register.mako'
	base_template = 'sapyens.views:templates/base.mako'
	permission = pyramid.security.NO_PERMISSION_REQUIRED
	form_class = RegForm
	redirect_route = 'register.continue'
	callback_route = 'register.callback'
	email_sender = 'robot@example.com'
	email_subject = "Registration"
	email_renderer = 'sapyens.views:templates/register/registration_email.mako'
	user_model = None  #abstract
	code_model = None  #abstract
	page_title = 'Register'
	include_services = True
	include_email_form = True

	@classmethod
	def include_to_config (self, config):
		config.add_route(self.route_name, self.route_path)
		config.add_view(self(), route_name = self.route_name, renderer = self.renderer, permission = self.permission)

	def __call__ (self, context, request):
		form = self.form_class(request.POST)
		result = {
			'form': form,
			'base_template': self.base_template,
			'page_title': self.page_title,
			'include_services': self.include_services,
			'include_email_form': self.include_email_form,
			'service_redirect_urls': {'google': request.route_path(sapyens.views.GoogleRegisterRedirectView.route_name)},
		}
		if request.method == 'POST':
			if form.validate():
				if self._after_validated(context, request, form, result):
					return HTTPFound(location = request.route_url(self.redirect_route))
				else:
					return result	
			else:
				return result
		else:
			return result

	def _after_validated (self, context, request, form, result):
		user = self._fetch_user(form, form)
		if user:
			form.errors['email'] = ["User already exists"]
		else:
			return self._on_continue(form, request)

	def _fetch_user (self, form):
		return user_model.query.filter_by(email = form.email.data).first()

	def _on_continue (self, form, request):
		code = self._create_callback_code(code, form)
		callback_url = request.route_url(self.callback_route, code = code)
		message = self._make_message(form, callback_url, request)
		get_mailer(request).send()
		return True

	def _create_callback_code (self, code, form):
		code = base64.urlsafe_b64encode(os.urandom(69))  #number is arbitrary but avoids trailing '='s
		#TODO hash pwd
		#TODO use dbsession
		#TODO handle duplication
		self.code_model(id = code, email = form.email.data, password = form.password.data).add()
		return code

	def _make_message (self, form, callback_url, request):
		return Message(
			subject = self.email_sender,
			sender = self.email_subject,
			recipients = [form.email.data],
			html = render(self.email_renderer, {'url': callback_url}, request)
		)

class RegisterCallbackView (object):
	route_name = RegisterView.callback_route
	route_path = '/register.confirm_email/{code}'
	# renderer = '...'
	# base_template = 'sapyens.views:templates/base.mako'
	permission = RegisterView.permission
	code_model = None  #abstract
	user_model = None  #abstract
	code_timeout = datetime.timedelta(days = 3)
	redirect_route = None

	@classmethod
	def include_to_config (self, config):
		config.add_route(self.route_name, self.route_path)
		# config.add_view(self, route_name = self.route_name, renderer = self.renderer, permission = self.permission)
		config.add_view(self(), route_name = self.route_name, permission = self.permission)

	def __call__ (self, context, request):
		code = self._fetch_code(request)
		if datetime.datetime.utcnow() - code.created_time > self.code_timeout:
			#TODO friendly message
			return HTTPNotFound()

		self._on_success(request, code)

		code.delete()

		#TODO copypaste, cooperate with login view
		url = request.route_url(self.redirect_route) if redirect_route else request.application_url
		response = HTTPFound(location = url)
		response = self._sign_in(request, response, code.email)
		return response

	def _sign_in (self, request, response, userid):
		response.headerlist.extend(pyramid.security.remember(request, userid))
		return response

	def _on_success (self, request, code):
		#TODO hash password
		self.user_model(email = code.email, password = code.password).add()
		#TODO handle duplication

	def _fetch_code (self, request):
		code = request.matchdict['code']
		#TODO friendly message if absent
		return self.code_model.try_get(code)
