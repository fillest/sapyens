#coding: utf-8
import unittest
import subprocess
import pyramid.paster
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker


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

		subprocess.check_call('python src/sapyens/migrate.py %s --engine postgresql --final-to-apply 2' % cfg_path, shell = True)
		self.assertEqual(db_session.execute('select * from test').fetchall(), [(u'test',)])

		msg = subprocess.check_output('python src/sapyens/migrate.py %s --engine postgresql --final-to-apply 3; true' % cfg_path,
			shell = True, stderr=subprocess.STDOUT)
		self.assertIn('Ambiguous migration index', msg)

		msg = subprocess.check_output('python src/sapyens/migrate.py %s --engine postgresql --final-to-apply 2; true' % cfg_path,
			shell = True, stderr=subprocess.STDOUT)
		self.assertIn('is not pending', msg)

		db_session.close()
