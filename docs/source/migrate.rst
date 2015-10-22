About
-----

**sapyens.migrate** manages SQL migrations. Migrations are plain files
with SQL statements. To track which migrations are already applied, for
each migration a record is created in a dedicated table in your
database.

This system is handy with `reflection`_ to minimize ORM boilerplate.

Setup
-----


1. ``cd`` to you project
2. Add entry point to setup.py:

 .. code-block:: python

    setup(name = 'mypackage',
      #...
      entry_points = """
          #...
          [console_scripts]
              migrate = sapyens.migrate:run
      """,
3. Create migration dir, e.g. ``mypackage/db/migrations``
4. Update your config:
 .. code-block:: ini

    [app:main]
    #...
    sapyens.migrate.dir_path = mypackage/db/migrations
    #sapyens.migrate.table_name = some_name #if you want to change default name 'migrations'


5. Make the script available as “migrate” in environment:

    .. code-block:: console
        bash  pip install -e .

Usage and workflow
------------------

1. Create your migration, e.g. ``mypackage/db/migrations/0001_init.sql``
   (you can do it also by executing
   ``migrate home.ini --create-next init``)
2. Run ``migrate dev.ini`` (pass your config). You should see something like:
 .. code-block:: console

    (venv)f@host:~/proj/mypackage$ migrate dev.ini
    2012-09-13 02:30:12,853 INFO  [sapyens.migrate][MainThread] Creating migration table 'migrations'
    2012-09-13 02:30:13,009 INFO  [sapyens.migrate][MainThread] Applying migration mypackage/db/migrations/0001_init.sql

3. Script detects the order of the migrations by sorting file names, so increment number for the next one: ``0002_blah.sql``. You may use ``--create-next`` (or ``-cn`` shortcut) to automate file creation:
 .. code-block:: console

    (venv)f@host:~/proj/mypackage$ migrate dev.ini -cn "change some table"
    2012-09-18 00:40:35,997 INFO  [sapyens.migrate][MainThread] Creating file mypackage/db/migrations/0002_change_some_table.sql
4. During development you may make actual changes in `pgAdmin`_ first and then dump generated SQL to a file, so on next ``migrate`` you will get an error (bacause of applying changes that are already applied). To “mark” such migration as already applied, you can force migration record creation without actually applying its content (with ``--force-write`` or ``-fw``):
 .. code-block:: console

    #you can use index
    migrate dev.ini -fw 1 2
    #or path
    migrate dev.ini -fw mypackage/db/migrations/0001_init.sql mypackage/db/migrations/0002_blah.sql
5. ``migrate --help`` to view other arguments and summary

Logging
-------

 **sapyens.migrate** uses standard Python logging. During local development you may keep your Pyramid root logger with INFO level, but in production you may want to switch it to WARN, so to see migration messages during deploy you can modify your config accordingly:

 .. code-block:: ini

    [loggers]
    keys = root, mypackage, sqlalchemy, migrate

    [logger_migrate]
    level = INFO
    handlers = 
    qualname = sapyens.migrate

.. _reflection: http://docs.sqlalchemy.org/en/rel_0_9/orm/extensions/declarative.html#using-reflection-with-declarative
.. _pgAdmin: http://www.pgadmin.org/