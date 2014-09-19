from pyramid.security import authenticated_userid, has_permission
import pyramid.tweens
from pyramid.settings import asbool


def includeme (config):
	settings = config.get_settings()

	#TODO maybe better turn off by default?
	if asbool(settings.get('sapyens.add_static_view', True)):
		#TODO configurable attrs
		add_static_view(config)

	# if has_permission_prop:
	# 	config.set_request_property(
	# 		lambda request: lambda permission: has_permission(permission, request.root, request),
	# 		'has_permission'
	# 	)

	if asbool(settings.get('sapyens.db_not_found_tween', True)):
		config.add_tween('sapyens.db.notfound_tween_factory', under = pyramid.tweens.EXCVIEW)

def add_static_view (config, cache_max_age = 3600):
	config.add_static_view('sapyens.static', 'sapyens:static/', cache_max_age = cache_max_age)
