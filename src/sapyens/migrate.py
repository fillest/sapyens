import argparse
import pyramid.paster
import logging.config
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc
import glob
import os.path
import logging


MIGRATIONS_TABLE_SQL = """
	CREATE TABLE {table_name}
	(
	   id text,
	   applied_time timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now()),
		PRIMARY KEY (id)
	);
"""


def make_script_entry_point (migrations_dir, migrations_table_name = 'migrations'):
	if not os.path.isdir(migrations_dir):
		raise ValueError("specified path is not valid dir path: %s" % migrations_dir)

	def main ():
		opts = _parse_opts()

		pyramid.paster.setup_logging(opts.config)
		log = logging.getLogger(__name__)

		settings = pyramid.paster.get_appsettings(opts.config)
		db_session = sessionmaker(bind = engine_from_config(settings, 'sqlalchemy.'))()

		applied_migrations = _get_applied_migrations(migrations_table_name, db_session, log)
		avail_mirgations = set(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(migrations_dir + '/*.sql'))
		pending_migrations = sorted(avail_mirgations - applied_migrations)

		_apply_migrations(pending_migrations, migrations_dir, migrations_table_name, db_session, log, opts.force_write)

	return main

def _parse_opts ():
	parser = argparse.ArgumentParser()
	parser.add_argument('config', help = "config file")
	parser.add_argument('-fw', '--force-write', nargs = '*', help = "write migration records without applying their content", default = [])
	return parser.parse_args()

def _get_applied_migrations (migrations_table_name, db_session, log):
	applied_migrations = set()
	try:
		applied_migrations = set(id for (id,) in db_session.execute('SELECT id FROM %s' % migrations_table_name))
	except sqlalchemy.exc.ProgrammingError as e:
		if ('relation "%s" does not exist' % migrations_table_name) in str(e):
			db_session.rollback()

			log.info("Creating table '%s'" % migrations_table_name)
			db_session.execute(MIGRATIONS_TABLE_SQL.format(table_name = migrations_table_name))
			db_session.commit()
		else:
			raise
	return applied_migrations

def _apply_migrations (migrations, migrations_dir, migrations_table_name, db_session, log, migrations_to_force_write):
	if migrations:
		for migration_id in migrations:
			fpath = _migration_path(migrations_dir, migration_id)
			log.info("Applying " + fpath)
			with open(fpath, 'rb') as f:
				if migration_id not in _paths_to_ids(migrations_to_force_write, migrations_dir):
					db_session.execute(f.read())
				db_session.execute('INSERT INTO %s (id) VALUES (:id)' % migrations_table_name, {
					'id': migration_id,
				})
		db_session.commit()

def _paths_to_ids (paths, migrations_dir):
	for path in paths:
		migration_id, _ext = os.path.splitext(os.path.basename(path))
		p = _migration_path(migrations_dir, migration_id)
		if not os.path.isfile(p):
			raise ValueError(path)
		yield migration_id

def _migration_path (dir_path, migration_id):
	return dir_path + '/%s.sql' % migration_id
