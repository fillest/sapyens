#coding: utf-8
import unittest
import subprocess
import pyramid.paster
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc


def stub_loader_for_migrate ():
	pass

class TestMigrate (unittest.TestCase):
	def test_utf8_content (self):
		cfg_path = 'src/sapyens/tests/migrate/utf8_content.ini'
		settings = pyramid.paster.get_appsettings(cfg_path)
		db_session = sessionmaker(bind = engine_from_config(settings, 'sqlalchemy.'))()

		db_session.execute('drop table if exists test')
		db_session.execute('drop table if exists migrations')
		db_session.commit()

		subprocess.check_call('python src/sapyens/migrate.py %s --engine postgresql' % cfg_path, shell = True)
		self.assertEqual(db_session.execute('select * from test').fetchall(), [(u'тест',)])

		db_session.close()

	def test_final_to_apply (self):
		cfg_path = 'src/sapyens/tests/migrate/final_to_apply.ini'
		settings = pyramid.paster.get_appsettings(cfg_path)
		db_session = sessionmaker(bind = engine_from_config(settings, 'sqlalchemy.'))()

		db_session.execute('drop table if exists test')
		db_session.execute('drop table if exists migrations')
		db_session.commit()

		msg = subprocess.check_output('python src/sapyens/migrate.py %s --engine postgresql --final-to-apply 123; true' % cfg_path,
			shell = True, stderr=subprocess.STDOUT)
		self.assertIn('ValueError: Invalid migration index', msg)

		subprocess.check_call('python src/sapyens/migrate.py %s --engine postgresql --final-to-apply 2' % cfg_path, shell = True)
		self.assertEqual(db_session.execute('select * from test').fetchall(), [(u'test',)])

		msg = subprocess.check_output('python src/sapyens/migrate.py %s --engine postgresql --final-to-apply 3; true' % cfg_path,
			shell = True, stderr=subprocess.STDOUT)
		self.assertIn('Ambiguous migration index', msg)

		msg = subprocess.check_output('python src/sapyens/migrate.py %s --engine postgresql --final-to-apply 2; true' % cfg_path,
			shell = True, stderr=subprocess.STDOUT)
		self.assertIn('is not pending', msg)

		db_session.close()

	def test_force_write (self):
		cfg_path = 'src/sapyens/tests/migrate/force_write.ini'
		settings = pyramid.paster.get_appsettings(cfg_path)
		db_session = sessionmaker(bind = engine_from_config(settings, 'sqlalchemy.'))()

		db_session.execute('drop table if exists test')
		db_session.execute('drop table if exists migrations')
		db_session.commit()

		msg = subprocess.check_output('python src/sapyens/migrate.py %s --engine postgresql -fw 12; true' % cfg_path,
			shell = True, stderr=subprocess.STDOUT)
		self.assertIn('ValueError: Invalid migration index', msg)

		subprocess.check_call('python src/sapyens/migrate.py %s --engine postgresql -fw 1 2' % cfg_path, shell = True)
		self.assertEqual(db_session.execute('select count(*) from migrations').scalar(), 2)
		try:
			db_session.execute('select * from test').fetchall()
		except sqlalchemy.exc.ProgrammingError as e:
			if 'relation "test" does not exist' not in str(e):
				raise
		else:
			self.fail()
		db_session.close()

	def test_file_names (self):
		cfg_path = 'src/sapyens/tests/migrate/file_names.ini'
		settings = pyramid.paster.get_appsettings(cfg_path)
		db_session = sessionmaker(bind = engine_from_config(settings, 'sqlalchemy.'))()

		db_session.execute('drop table if exists test')
		db_session.execute('drop table if exists migrations')
		db_session.commit()

		msg = subprocess.check_output('python src/sapyens/migrate.py %s --engine postgresql; true' % cfg_path,
			shell = True, stderr=subprocess.STDOUT)
		# self.assertEqual(db_session.execute('select * from test').fetchall(), [(u'1',), (u'4',)])
		self.assertIn('test.sql', msg)
		self.assertIn('000_test.sql', msg)

		db_session.close()
