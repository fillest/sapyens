import argparse
import pyramid.paster
import logging


class Script (object):
	def _init_parser (self):
		parser = argparse.ArgumentParser()
		parser.add_argument('config', help = "config file")
		return parser

	def _setup_arg_parser (self, parser):
		pass

	def run (self, args, settings, log):
		raise NotImplementedError()

	def main (self):
		parser = self._init_parser()
		self._setup_arg_parser(parser)
		args = parser.parse_args()

		pyramid.paster.setup_logging(args.config)
		log = logging.getLogger(__name__)

		settings = pyramid.paster.get_appsettings(args.config)

		self.run(args, settings, log)
