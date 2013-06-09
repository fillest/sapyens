def add_static_route (config, cache_max_age = 3600):
	config.add_static_view('sapyens.static', 'sapyens:static/', cache_max_age = cache_max_age)
