#coding: utf-8
import argparse
import logging.config
import glob
import os.path
import logging
import re
import sys
import itertools
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc
import pyramid.paster


MIGRATION_TABLE_SQL = {
	'postgresql': 
		"""
			CREATE TABLE {table_name}
			(
				id text,
				applied_time timestamp without time zone NOT NULL DEFAULT timezone('utc'::text, now()),
			
				PRIMARY KEY (id)
			);
		""",
	'mysql':
		# MySQL converts TIMESTAMP values from the current time zone to UTC for storage, and back from UTC to the current time zone for retrieval
		# http://dev.mysql.com/doc/refman/5.5/en/datetime.html
		"""
			CREATE TABLE {table_name}
			(
				id VARCHAR (200),
				applied_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

				PRIMARY KEY(id)
			);
		""",
}

DEFAULT_MIGRATION_TABLE_NAME = 'migrations'

ID_NUMBER_RE = re.compile(r'^(\d+)')


def _make_entry_point_function (get_migration_dir_path, get_migration_table_name):
	def run ():
		args = _parse_args()

		pyramid.paster.setup_logging(args.config)
		#can't just move logger to module level, setup_logging disables it
		log = logging.getLogger(__name__)

		settings = pyramid.paster.get_appsettings(args.config)
		db_session = sessionmaker(bind = engine_from_config(settings, 'sqlalchemy.'))()

		path = get_migration_dir_path(settings)
		_assert_migration_dir_exists(path)
		table_name = get_migration_table_name(settings)

		avail_paths = set(glob.glob(path + '/*.sql'))
		avail_ids = set(map(_path_to_id, avail_paths))
		applied_ids = _get_applied_ids_or_create_table(table_name, db_session, log, args.engine)

		if args.show:
			for mid in sorted(avail_ids):
				print "%s %s %s" % ((u"✓" if mid in applied_ids else " "),  mid, _sql_fpath(path, mid).rjust(70))
			return

		new_id = None
		if args.create_next:
			new_id = _create_next_migration_file(avail_ids, args.create_next, path, log)

		pending_ids = sorted(avail_ids - applied_ids)
		ids_to_force_write = set(_try_input_to_ids(args.force_write or [], avail_paths, log))
		if new_id and args.force_write is not None:
			ids_to_force_write.add(new_id)
			pending_ids.append(new_id)

		if args.final_to_apply:
			[id_final] = list(_try_input_to_ids([args.final_to_apply], avail_paths, log))
			if id_final not in pending_ids:
				log.error("Migration '%s' is not pending" % args.final_to_apply)
				sys.exit(1)
			pending_ids = list(itertools.takewhile(lambda mid: mid != id_final, pending_ids)) + [id_final]

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
		match = ID_NUMBER_RE.match(last).group(1)
		i_len = len(match)
		next_i = int(match) + 1
	else:
		next_i = 1
		i_len = len('000%s' % next_i)
	
	mid = "%s_%s" % (str(next_i).zfill(i_len), name.replace(" ", "_"))
	path = '%s/%s.sql' % (path, mid)
	log.info("Creating file " + path)
	os.close(os.open(path, os.O_CREAT | os.O_EXCL))

	return mid


def _assert_migration_dir_exists (path):
	if not os.path.isdir(path):
		raise ValueError(u"specified path is not valid dir path: %s" % path)

def _parse_args ():
	parser = argparse.ArgumentParser()
	parser.add_argument('-fw', '--force-write', nargs = '*', metavar = 'MIGRATION_INDEX_OR_FILE_PATH',
		help = "These migrations will be marked as applied without actually applying them"
			" (can be combined with --create-next without providing id)")
	parser.add_argument('-cn', '--create-next', metavar = 'NAME',
		help = "Create a migration file with next index")
	parser.add_argument('-s', '--show', action = 'store_true', help = "Show available/applied migrations and exit")
	parser.add_argument('-e', '--engine', help = "select your database engine type for creating migrations history table if it does not exist")
	parser.add_argument('-f', '--final-to-apply', help = "Stop applying after this migration (by default all pending migrations get applied)")
	parser.add_argument('config', help = "config file")
	return parser.parse_args()

def _get_applied_ids_or_create_table (migration_table_name, db_session, log, engine):
	applied_ids = set()
	try:
		applied_ids = set(id for (id,) in db_session.execute('SELECT id FROM %s' % migration_table_name))
	except sqlalchemy.exc.ProgrammingError as exception:
		if ('relation "%s" does not exist' % migration_table_name) in str(exception):
			db_session.rollback()

			_create_migration_table(migration_table_name, db_session, log, engine)
		else:
			raise
	return applied_ids

ENGINE_CHOICES = {
	'1': 'postgresql',
	'2': 'mysql',
}

def _engine_choice_dialog ():
	choice = raw_input("""\
Migration history table haven't been created in your database yet.
Please, enter an appropriate number of your database engine type:
1 PostgreSQL
2 MySQL
> """)

	if choice not in ENGINE_CHOICES:
		print 'Invalid choice.\n'
		return _engine_choice_dialog()

	return ENGINE_CHOICES[choice]

def _create_migration_table (migration_table_name, db_session, log, engine):
	if engine not in MIGRATION_TABLE_SQL:
		if engine in ENGINE_CHOICES:
			engine = ENGINE_CHOICES[engine]
		else:
			engine = _engine_choice_dialog()

	sql = MIGRATION_TABLE_SQL[engine]
	log.info("Creating migration table '%s'..." % migration_table_name)
	db_session.execute(sql.format(table_name = migration_table_name))
	db_session.commit()

def _apply_migrations (ids, migration_dir, table_name, db_session, log, ids_to_force_write):
	if ids:
		for migration_id in ids:
			fpath = _sql_fpath(migration_dir, migration_id)
			log.info("Applying migration '%s'..." % fpath)
			with open(fpath, 'rb') as f:
				if migration_id not in ids_to_force_write:
					code = f.read().decode('utf-8')
					db_session.execute(code)
				
				db_session.execute('INSERT INTO %s (id) VALUES (:id)' % table_name, {
					'id': migration_id,
				})
		db_session.commit()

def _sql_fpath (dir_path, migration_id):
	return '%s/%s.sql' % (dir_path, migration_id)

def _path_to_id (path):
	migration_id, _ext = os.path.splitext(os.path.basename(path))
	return migration_id

def _try_input_to_ids (input_migrations, avail_paths, log):
	assert isinstance(input_migrations, (list, tuple)), type(input_migrations)

	def raise_invalid (m):
		raise ValueError(u"Invalid migration index or path: %s" % m)

	for m in input_migrations:
		if m in avail_paths:
			yield _path_to_id(m)
		else:
			if m.isdigit():
				def match_index (path, m=m):
					return int(ID_NUMBER_RE.match(_path_to_id(path)).group(1)) == int(m)
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


if __name__ == '__main__':
	run()