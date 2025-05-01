import sys

# Tambahkan path project ke sys.path
project_home = '/home/gafarybyh/elephant_agent_bot'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import aplikasi Flask dari webhook_bot.py
from webhook_method.webhook_bot import app as application

# This is the WSGI entry point that PythonAnywhere looks for
if __name__ == '__main__':
    application.run()
