class Field (object):
	pass

class Unicode (Field):
	def __init__ (self, blank = '', min_len = 0):
		self._blank_value = blank
		self._min_len = min_len

	def blank (self):
		return self._blank_value

	def get_parsed_value (self, raw_value):
		if isinstance(raw_value, unicode):
			return raw_value

		return unicode(raw_value, 'utf-8')

	def parse (self, raw_value):
		value = self.get_parsed_value(raw_value)

		if len(value) >= self._min_len:
			return True, value
		else:
			return False, raw_value

class MapperMeta (type):
	def __init__ (class_, name, bases, attrs):
		super(MapperMeta, class_).__init__(name, bases, attrs)
		for name, maybe_field in attrs.items():
			if isinstance(maybe_field, Field):
				class_._fields[name] = maybe_field

class Result (object):
	pass

class Mapper (object):
	__metaclass__ = MapperMeta

	_fields = {}

	def blank (self):
		result = Result()
		result.is_valid = True

		for k, field in self._fields.items():
			setattr(result, k, field.blank())

		return result

	def parse (self, source):
		result = Result()
		result.errors = {}
		result.is_valid = True

		def set_invalid (name, value):
			result.errors[name] = True
			result.is_valid = False
			setattr(result, name, value)

		for name, field in self._fields.items():
			if name in source:
				is_valid, value = field.parse(source[name])
				if is_valid:
					setattr(result, name, value)
				else:
					set_invalid(name, source[name])
			else:
				set_invalid(name, '')

		#TODO if invalid, overwrite valid values with source?

		return result

	def parse_model (self, model):
		result = Result()
		result.is_valid = True

		for name, _field in self._fields.items():
			setattr(result, name, getattr(model, name))

		return result

	def fill_model (self, model, result):
		for name, _field in self._fields.items():
			assert hasattr(model, name)
			setattr(model, name, getattr(result, name))
