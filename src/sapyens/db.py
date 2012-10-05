import logging
from contextlib import contextmanager
import collections
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, mapper
from sqlalchemy import Table
from sqlalchemy.orm.util import _is_mapped_class
#NOTE conditional zope.sqlalchemy import in make_classes() below
#NOTE pyramid.httpexceptions.HTTPNotFound import in notfound_tween_factory() below


@contextmanager
def engine_log_level (level):
	db_logger = logging.getLogger('sqlalchemy.engine')
	old_level = db_logger.level

	db_logger.level = level
	try:
		yield
	finally:
		db_logger.level = old_level


#TODO will be obsolete in sqla0.8 (see DeferredReflection)
#see http://docs.sqlalchemy.org/en/rel_0_7/orm/examples.html#declarative-reflection
#see http://hg.sqlalchemy.org/sqlalchemy/file/8e1b23314c39/examples/declarative_reflection/declarative_reflection.py
#see https://bitbucket.org/zzzeek/sqlalchemy/pull-request/1/copied-declarativereflectedbase-from-the
class DeclarativeReflectedBase(object):
    _mapper_args = []

    @classmethod
    def __mapper_cls__(cls, *args, **kw):
        """Declarative will use this function in lieu of
        calling mapper() directly.

        Collect each series of arguments and invoke
        them when prepare() is called.
        """

        cls._mapper_args.append((args, kw))

    @classmethod
    def prepare(cls, engine):
        """Reflect all the tables and map !"""
        while cls._mapper_args:
            args, kw  = cls._mapper_args.pop()
            klass = args[0]
            # autoload Table, which is already
            # present in the metadata.  This
            # will fill in db-loaded columns
            # into the existing Table object.
            if args[1] is not None:
                table = args[1]
                Table(table.name,
                    cls.metadata,
                    extend_existing=True,
                    autoload_replace=False,
                    autoload=True,
                    autoload_with=engine,
                    schema=table.schema)

            # see if we need 'inherits' in the
            # mapper args.  Declarative will have
            # skipped this since mappings weren't
            # available yet.
            for c in klass.__bases__:
                if _is_mapped_class(c):
                    kw['inherits'] = c
                    break

            klass.__mapper__ = mapper(*args, **kw)


class NotFound (Exception):
	pass

#DBObject = declarative_base()
#DBObject = declarative_base(cls = DeclarativeReflectedBase)
#class Reflected (DeclarativeReflectedBase, DBObject):
class Reflected (DeclarativeReflectedBase, declarative_base()):
	__abstract__ = True

	def __repr__ (self):
		return u"<{module}.{class_name} #{id}>".format(
			module = self.__class__.__module__,
			class_name = self.__class__.__name__,
			id = self.id,
		)

	@classmethod
	def try_get (cls, **kwargs):
		obj = cls.query.filter_by(**kwargs).first()
		if obj:
			return obj
		else:
			raise NotFound()

	def set (self, **fields):
		for name, value in fields.items():
			setattr(self, name, value)
		return self


def notfound_tween_factory (handler, _registry):
	from pyramid.httpexceptions import HTTPNotFound

	def tween (request):
		try:
			response = handler(request)
		except NotFound:
			raise HTTPNotFound()

		return response
	return tween


def make_classes (use_zope_ext = True):
	if use_zope_ext:
		from zope.sqlalchemy import ZopeTransactionExtension

	DBSession = scoped_session(sessionmaker(
		extension = ZopeTransactionExtension() if use_zope_ext else None
	))

	class QueryPropertyMixin (object):
		query = DBSession.query_property()

	class ScopedSessionMixin (object):
		def add (self):
			DBSession.add(self)
			return self

		def delete (self):
			DBSession.delete(self)
			return self

		def flush (self):
			DBSession.flush()
			return self

		def commit (self):
			DBSession.commit()
			return self

	return collections.namedtuple('Classes', ('DBSession', 'QueryPropertyMixin', 'ScopedSessionMixin'))(
		DBSession, QueryPropertyMixin, ScopedSessionMixin
	)


def init (engine, DBSession, Reflected, on_before_reflect = None):
	DBSession.configure(bind = engine)

	#DBObject.metadata.bind = engine
	Reflected.metadata.bind = engine

	with engine_log_level(logging.WARN):
		if on_before_reflect:
			on_before_reflect()

		Reflected.prepare(engine)
