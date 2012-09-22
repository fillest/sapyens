import argparse
import pyramid.paster
import logging.config
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc
import glob
import os.path
import logging
import re
import sys


MIGRATION_TABLE_SQL = """
	CREATE TABLE {table_name}
	(
	   id text,
	   applied_time timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now()),
		PRIMARY KEY (id)
	);
"""

DEFAULT_MIGRATION_TABLE_NAME = 'migrations'

RE_ID_N = re.compile(r'^(\d+)')


def _make_entry_point_function (get_migration_dir_path, get_migration_table_name):
	def run ():
		args = _parse_args()

		pyramid.paster.setup_logging(args.config)
		log = logging.getLogger(__name__) #TODO move to module-level?
		settings = pyramid.paster.get_appsettings(args.config)
		db_session = sessionmaker(bind = engine_from_config(settings, 'sqlalchemy.'))()

		path = get_migration_dir_path(settings)
		_assert_migration_dir_exists(path)
		table_name = get_migration_table_name(settings)

		avail_paths = set(glob.glob(path + '/*.sql'))
		avail_ids = set(map(_path_to_id, avail_paths))

		if args.create_next:
			return _create_next_migration_file(avail_ids, args.create_next, path, log)

		applied_ids = _get_applied_ids_or_create_table(table_name, db_session, log)
		pending_ids = sorted(avail_ids - applied_ids)
		ids_to_force_write = set(_try_process_force_write(args.force_write, avail_paths, log))

		_apply_migrations(pending_ids, path, table_name, db_session, log, ids_to_force_write)
	return run

run = _make_entry_point_function(
	lambda settings: settings['sapyens.migrate.dir_path'],
	lambda settings: settings.get('sapyens.migrate.table_name', DEFAULT_MIGRATION_TABLE_NAME),
)

def make_entry_point (migration_dir, migration_table_name = DEFAULT_MIGRATION_TABLE_NAME):
	_assert_migration_dir_exists(migration_dir)
	return _make_entry_point_function(lambda _s: migration_dir, lambda _s: migration_table_name)


def _create_next_migration_file (avail_ids, name, path, log):
	if avail_ids:
		last = sorted(avail_ids)[-1]
		match = RE_ID_N.match(last).group(1)
		i_len = len(match)
		next_i = int(match) + 1
	else:
		next_i = 1
		i_len = len('000%s' % next_i)
	
	path = '%s/%s_%s.sql' % (path, str(next_i).zfill(i_len), name.replace(" ", "_"))
	log.info("Creating file " + path)
	os.close(os.open(path, os.O_CREAT | os.O_EXCL))


def _assert_migration_dir_exists (path):
	if not os.path.isdir(path):
		raise ValueError(u"specified path is not valid dir path: %s" % path)

def _parse_args ():
	parser = argparse.ArgumentParser()
	parser.add_argument('config', help = "config file")
	parser.add_argument('-fw', '--force-write', nargs = '*', metavar = 'MIGRATION_INDEX_OR_FILE_PATH',
		help = "write migration records to DB without applying their content", default = [])
	parser.add_argument('-cn', '--create-next', metavar = 'NAME',
		help = "create next migration file and terminate")
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

def _apply_migrations (migration_ids, migration_dir, table_name, db_session, log, migration_ids_to_force_write):
	if migration_ids:
		for migration_id in migration_ids:
			sql_fpath = _sql_fpath(migration_dir, migration_id)
			log.info("Applying migration " + sql_fpath)
			with open(sql_fpath, 'rb') as f:
				if migration_id not in migration_ids_to_force_write:
					db_session.execute(f.read())
				db_session.execute('INSERT INTO %s (id) VALUES (:id)' % table_name, {
					'id': migration_id,
				})
		db_session.commit()

def _sql_fpath (dir_path, migration_id):
	return '%s/%s.sql' % (dir_path, migration_id)

def _path_to_id (path):
	migration_id, _ext = os.path.splitext(os.path.basename(path))
	return migration_id

def _try_process_force_write (input_migrations, avail_paths, log):
	def raise_invalid (m):
		raise ValueError(u"Invalid migration index or path: %s" % m)

	for m in input_migrations:
		if m in avail_paths:
			yield _path_to_id(m)
		else:
			if m.isdigit():
				def match_index (path, m=m):
					return int(RE_ID_N.match(_path_to_id(path)).group(1)) == int(m)
				paths = filter(match_index, avail_paths)

				if paths:
					if len(paths) == 1:
						yield _path_to_id(paths[0])
					else:
						log.error('Ambiguous migration index "%s". Pass full path instead:\n\t%s' % (m, "\n\t".join(paths)))
						sys.exit(1)
				else:
					raise_invalid(m)
			else:
				raise_invalid(m)