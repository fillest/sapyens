def add_static_route (config):
	config.add_static_view('sapyens.static', 'sapyens:static/', cache_max_age = 3600)
