from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from hashlib import md5
from time import time
import jwt
from app import app
from datetime import datetime


followers = db.Table('followers',
	db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)  

class User(UserMixin,db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.DateTime, default=datetime.utcnow)

	def __repr__(self):
		return '<User {}>'.format(self.username)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)    

	def avatar(self, size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
			digest, size)

	
	followed = db.relationship(
		'User', secondary=followers,
		primaryjoin=(followers.c.follower_id == id),
		secondaryjoin=(followers.c.followed_id == id),
		backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')   


	def follow(self, user):
		if not self.is_following(user):
			self.followed.append(user)

	def unfollow(self, user):
		if self.is_following(user):
			self.followed.remove(user)

	def is_following(self, user):
		return self.followed.filter(
			followers.c.followed_id == user.id).count() > 0 

	def followed_posts(self):
		followed = Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id)
		own = Post.query.filter_by(user_id=self.id)
		return followed.union(own).order_by(Post.timestamp.desc())	



	def get_reset_password_token(self, expires_in=600):
		return jwt.encode(
			{'reset_password': self.id, 'exp': time() + expires_in},
			app.config['SECRET_KEY'], algorithm='HS256')

	@staticmethod
	def verify_reset_password_token(token):
		try:
			id = jwt.decode(token, app.config['SECRET_KEY'],
							algorithms=['HS256'])['reset_password']
		except:
			return
		return User.query.get(id)		


	
	liked = db.relationship('PostLike',
		foreign_keys='PostLike.user_id',
		backref='user', lazy='dynamic')

	def like_post(self, post):
		if not self.has_liked_post(post):
			like = PostLike(user_id=self.id, post_id=post.id)
			db.session.add(like)

	def unlike_post(self, post):
		if self.has_liked_post(post):
			PostLike.query.filter_by(
				user_id=self.id,
				post_id=post.id).delete()

	def has_liked_post(self, post):
		return PostLike.query.filter(
			PostLike.user_id == self.id,
			PostLike.post_id == post.id).count() > 0
			


class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	# comment = db.relationship('Comment', backref='author', lazy='dynamic')

	def __repr__(self):
		return '<Post {}>'.format(self.body)

	language = db.Column(db.String(5))

	likes = db.relationship('PostLike', backref='post', lazy='dynamic')



@login.user_loader
def load_user(id):
	return User.query.get(int(id))


# class Comment(db.Model):
# 	_N = 6

# 	id = db.Column(db.Integer, primary_key=True)
# 	text = db.Column(db.String(140))
# 	author = db.Column(db.String(32))
# 	timestamp = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
# 	path = db.Column(db.Text, index=True)
# 	parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
# 	replies = db.relationship(
# 		'Comment', backref=db.backref('parent', remote_side=[id]),
# 		lazy='dynamic')

# 	def save(self):
# 		db.session.add(self)
# 		db.session.commit()
# 		prefix = self.parent.path + '.' if self.parent else ''
# 		self.path = prefix + '{:0{}d}'.format(self.id, self._N)
# 		db.session.commit()

# 	def level(self):
# 		return len(self.path) // self._N - 1

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(140))
    author = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

  


class PostLike(db.Model):
	__tablename__ = 'post_like'
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
