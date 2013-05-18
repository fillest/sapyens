import os.path
import setuptools


parent_dir_path = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(parent_dir_path, 'readme.md'), 'r') as f:
	readme_content = f.read()

setuptools.setup(
	name = 'sapyens',
	version = '0.2.1',
	description = 'SQLAlchemy & Pyramid enhancements',
	long_description = readme_content,
	author = 'Philipp Saveliev',
	author_email = 'fsfeel@gmail.com',
	url = 'https://github.com/fillest/sapyens',
	package_dir = {'': 'src'},
	packages = setuptools.find_packages('src'),
	include_package_data = True,
	zip_safe = False,
	classifiers = [
		'Development Status :: 4 - Beta',
		'Framework :: Pyramid',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python',
	],
	entry_points = """\
		[pyramid.scaffold]
			sapyens=sapyens.scaffolds:SapyensTemplate
	"""
)
