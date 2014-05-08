import unittest
from sapyens import crud
from mock import MagicMock, NonCallableMagicMock
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Text
from wtforms.ext.csrf.fields import CSRFTokenField
from wtforms.fields.simple import BooleanField
from wtforms.fields.core import StringField


class TestMakeForm (unittest.TestCase):
	def test_1 (self):
		class User (declarative_base()):
			__tablename__ = 'users'
			id = Column(Integer, primary_key=True)
			name = Column(String)
			email = Column(Text)
			is_active = Column(Boolean)
		Form = crud.make_form(User)
		fields = list(Form(csrf_context = NonCallableMagicMock()))

		expected_fields = [
			CSRFTokenField,
			StringField,
			StringField,
			BooleanField,
		]
		self.assertEqual(len(fields), len(expected_fields))
		for f, ef in zip(fields, expected_fields):
			self.assertIsInstance(f, ef)
