import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
	
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
		'sqlite:///' + os.path.join(basedir, 'app_1.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	MAIL_SERVER = os.environ.get('MAIL_SERVER') or "smtp.gmail.com"
	MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
	MAIL_USE_TLS = True
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	ADMINS = ['chanchaldhawan59@gmail.com']

	# POSTS_PER_PAGE = 3
	POSTS_PER_PAGE = 25

	LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')