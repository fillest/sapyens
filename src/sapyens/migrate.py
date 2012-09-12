import argparse
import pyramid.paster
import logging.config
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc
import glob
import os.path
import logging


MIGRATION_TABLE_SQL = """
	CREATE TABLE {table_name}
	(
	   id text,
	   applied_time timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now()),
		PRIMARY KEY (id)
	);
"""

DEFAULT_MIGRATION_TABLE_NAME = 'migrations'


def _make_entry_point_function (get_migration_dir_path, get_migration_table_name):
	def run ():
		opts = _parse_args()

		pyramid.paster.setup_logging(opts.config)
		log = logging.getLogger(__name__)

		settings = pyramid.paster.get_appsettings(opts.config)
		db_session = sessionmaker(bind = engine_from_config(settings, 'sqlalchemy.'))()
		path = get_migration_dir_path(settings)
		_check_migration_dir(path)
		table_name = get_migration_table_name(settings)

		applied_ids = _get_applied_ids_or_create_table(table_name, db_session, log)
		avail_ids = set(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(path + '/*.sql'))
		pending_ids = sorted(avail_ids - applied_ids)

		_apply_migrations(pending_ids, path, table_name, db_session, log, opts.force_write)
	return run

run = _make_entry_point_function(
	lambda settings: settings['sapyens.migrate.dir_path'],
	lambda settings: settings.get('sapyens.migrate.table_name', DEFAULT_MIGRATION_TABLE_NAME),
)

def make_entry_point (migration_dir, migration_table_name = DEFAULT_MIGRATION_TABLE_NAME):
	_check_migration_dir(migration_dir)
	return _make_entry_point_function(lambda _s: migration_dir, lambda _s: migration_table_name)


def _check_migration_dir (path):
	if not os.path.isdir(path):
		raise ValueError(u"specified path is not valid dir path: %s" % path)

def _parse_args ():
	parser = argparse.ArgumentParser()
	parser.add_argument('config', help = "config file")
	parser.add_argument('-fw', '--force-write', nargs = '*', metavar = 'MIGRATION_FILE_PATH',
		help = "write migration records to DB without applying their content", default = [])
	return parser.parse_args()

def _get_applied_ids_or_create_table (migration_table_name, db_session, log):
	applied_ids = set()
	try:
		applied_ids = set(id for (id,) in db_session.execute('SELECT id FROM %s' % migration_table_name))
	except sqlalchemy.exc.ProgrammingError as exception:
		if ('relation "%s" does not exist' % migration_table_name) in str(exception):
			db_session.rollback()

			log.info("Creating migration table '%s'" % migration_table_name)
			db_session.execute(MIGRATION_TABLE_SQL.format(table_name = migration_table_name))
			db_session.commit()
		else:
			raise
	return applied_ids

def _apply_migrations (migration_ids, migration_dir, migration_table_name, db_session, log, migrations_to_force_write):
	if migration_ids:
		for migration_id in migration_ids:
			fpath = _migration_path(migration_dir, migration_id)
			log.info("Applying migration " + fpath)
			with open(fpath, 'rb') as f:
				if migration_id not in _paths_to_ids(migrations_to_force_write, migration_dir):
					db_session.execute(f.read())
				db_session.execute('INSERT INTO %s (id) VALUES (:id)' % migration_table_name, {
					'id': migration_id,
				})
		db_session.commit()

def _paths_to_ids (paths, migration_dir):
	for path in paths:
		migration_id, _ext = os.path.splitext(os.path.basename(path))
		p = _migration_path(migration_dir, migration_id)
		if not os.path.isfile(p):
			raise ValueError(path)
		yield migration_id

def _migration_path (dir_path, migration_id):
	return dir_path + '/%s.sql' % migration_id
