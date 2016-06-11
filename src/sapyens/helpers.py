import os
import time
import contextlib
import venusian
from pyramid.httpexceptions import HTTPNotFound


class add_route (object):
	def __init__(self, *params):
		self._params = params

	def register(self, scanner, name, wrapped):
		scanner.config.add_route(*self._params)

	def __call__(self, wrapped):
		venusian.attach(wrapped, self.register)
		return wrapped

#TODO how to just combine decorators?
class route_view_config (object):
	def __init__(self, path, route_name, **view_config_params):
		self._path = path
		self._route_name = route_name
		self._view_config_params = view_config_params

	def register(self, scanner, name, wrapped):
		scanner.config.add_route(self._route_name, self._path)

		scanner.config.add_view(wrapped, route_name = self._route_name, **self._view_config_params)

	def __call__(self, wrapped):
		venusian.attach(wrapped, self.register)
		return wrapped

class include_to_config (object):
	def register(self, scanner, name, wrapped):
		wrapped.include_to_config(scanner.config)

	def __call__(self, wrapped):
		venusian.attach(wrapped, self.register)
		return wrapped


def raise_not_found ():
	raise HTTPNotFound()



@contextlib.contextmanager
def change_cwd (path):
	old_dir = os.getcwd()
	os.chdir(path)
	try:
		yield old_dir
	finally:
		os.chdir(old_dir)
