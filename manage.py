#!/usr/bin/env python
import os, sys

sys.path.append('/srv')
sys.path.append('/srv/pydj')
sys.path.append('/srv/pydj/playlist')

try:
    # load MySQLdb interface emulation
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
