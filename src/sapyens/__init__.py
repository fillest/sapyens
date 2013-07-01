from pyramid.security import authenticated_userid, has_permission
import pyramid.tweens


def include (config,
		static_view = True,
		has_permission_prop = True,
		db_not_found_tween = True,
):
	if static_view:
		params = {} if static_view is True else static_view
		add_static_view(config, **params)

	if has_permission_prop:
		config.set_request_property(
			lambda request: lambda permission: has_permission(permission, request.root, request),
			'has_permission'
		)

	if db_not_found_tween:
		config.add_tween('sapyens.db.notfound_tween_factory', under = pyramid.tweens.EXCVIEW)

def add_static_view (config, cache_max_age = 3600):
	config.add_static_view('sapyens.static', 'sapyens:static/', cache_max_age = cache_max_age)
