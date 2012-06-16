import setuptools


requires = [
]


setuptools.setup(
	name = 'sapyens',
	version = '0.1',
	description = 'SQLAlchemy & Pyramid enhancements',
	author = 'Philipp Saveliev',
	author_email = 'fsfeel@gmail.com',
	url = 'https://github.com/fillest/sapyens',
	package_dir = {'': 'src'},
	packages = setuptools.find_packages('src'),
	include_package_data = True,
	zip_safe = False,
	install_requires = requires,
)
