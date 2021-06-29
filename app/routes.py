from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm
from flask_login import current_user, login_user, login_required
from app.models import User
from flask_login import logout_user
from flask import request
from werkzeug.urls import url_parse
from app import db
from app.forms import RegistrationForm
from datetime import datetime
from app.forms import EditProfileForm
from app.forms import EmptyForm
from app.forms import PostForm
from app.models import Post
from app.forms import ResetPasswordRequestForm
from app.email import send_password_reset_email
from app.forms import ResetPasswordForm
from flask import jsonify
from app.translate import translate
from flask import request
from app.forms import AddCommentForm
from app.models import Comment






@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
	tags = ['Traditional', 'General', 'Natural', 'Study', 'Sports','Select']
	form = PostForm()
	if request.method == 'POST':
		select_tag = request.form.get('post_tag')
	if form.validate_on_submit():
		if select_tag == 'Select':
			post = Post(body=form.post.data, author=current_user)
		else:
			post = Post(body=form.post.data, author=current_user, post_tag=select_tag)	
		db.session.add(post)
		db.session.commit()
		flash(f'Your post is now live!','info')
		return redirect(url_for('index'))
	page = request.args.get('page', 1, type=int)
	posts = current_user.followed_posts().paginate(
		page, app.config['POSTS_PER_PAGE'], False)
	# for i in posts.items:
	# 	if Comment.query.filter_by(post_id=i.id):
	# 		comment_count = Comment.query.filter_by(post_id=i.id).count()
	next_url = url_for('index', page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('index', page=posts.prev_num) \
		if posts.has_prev else None
	return render_template('index.html', title='Home', form=form,
						   posts=posts.items, next_url=next_url,
						   prev_url=prev_url, tags=tags)






@app.route('/explore')
@login_required
def explore():
	# posts = Post.query.order_by(Post.timestamp.desc()).all()
	# return render_template('index.html', title='Explore', posts=posts)
	page = request.args.get('page', 1, type=int)
	posts = Post.query.order_by(Post.timestamp.desc()).paginate(
		page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('explore', page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('explore', page=posts.prev_num) \
		if posts.has_prev else None
	return render_template("index.html", title='Explore', posts=posts.items,
						  next_url=next_url, prev_url=prev_url)




# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     # if current_user.is_authenticated:
#     #     return redirect(url_for('index'))
#     form = LoginForm()
#     if form.validate_on_submit():
#         # user = User.query.filter_by(username=form.username.data).first()
#         if form.username.data!='Abhay' and form.password.data!='hp':
#             flash('Invalid username or password')
#             return redirect(url_for('login'))
#         # login_user(user, remember=form.remember_me.data)
#         return redirect(url_for('index'))
#     return render_template('login.html', title='Sign In', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))

	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash(f'Invalid username or password','danger')
			return redirect(url_for('login'))
		login_user(user, remember=form.remember_me.data)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('index')
		return redirect(next_page)
		# return redirect(url_for('index'))
	return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(username=form.username.data, email=form.email.data)
		user.set_password(form.password.data)
		db.session.add(user)
		db.session.commit()
		flash(f'Congratulations, you are now a registered user!','success')
		return redirect(url_for('login'))
	return render_template('register.html', title='Register', form=form)    




@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page', 1, type=int)
	posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('user', username=user.username, page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('user', username=user.username, page=posts.prev_num) \
		if posts.has_prev else None
	form = EmptyForm()
	return render_template('user.html', user=user, posts=posts.items,
						   next_url=next_url, prev_url=prev_url, form=form)



@app.before_request
def before_request():
	if current_user.is_authenticated:
		current_user.last_seen = datetime.utcnow()
		db.session.commit()


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
	form = EditProfileForm(current_user.username)
	if form.validate_on_submit():
		current_user.username = form.username.data
		current_user.about_me = form.about_me.data
		db.session.commit()
		flash(f'Your changes have been saved.','success')
		return redirect(url_for('edit_profile'))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.about_me.data = current_user.about_me
	return render_template('edit_profile.html', title='Edit Profile',
						   form=form)       



@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
	form = EmptyForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=username).first()
		if user is None:
			flash('User {} not found.'.format(username))
			return redirect(url_for('index'))
		if user == current_user:
			flash('You cannot follow yourself!')
			return redirect(url_for('user', username=username))
		current_user.follow(user)
		db.session.commit()
		flash('You are following {}!'.format(username),'success')
		return redirect(url_for('user', username=username))
	else:
		return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
	form = EmptyForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=username).first()
		if user is None:
			flash('User {} not found.'.format(username))
			return redirect(url_for('index'))
		if user == current_user:
			flash('You cannot unfollow yourself!')
			return redirect(url_for('user', username=username))
		current_user.unfollow(user)
		db.session.commit()
		flash('You are not following {}.'.format(username),'info')
		return redirect(url_for('user', username=username))
	else:
		return redirect(url_for('index'))



@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = ResetPasswordRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			send_password_reset_email(user)
		flash('Check your email for the instructions to reset your password')
		return redirect(url_for('login'))
	return render_template('reset_password_request.html',
						   title='Reset Password', form=form)



@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	user = User.verify_reset_password_token(token)
	if not user:
		return redirect(url_for('index'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
		user.set_password(form.password.data)
		db.session.commit()
		flash('Your password has been reset.')
		return redirect(url_for('login'))
	return render_template('reset_password.html', form=form)    





@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
	return jsonify({'text': translate(request.form['text'],
									  request.form['source_language'],
									  request.form['dest_language'])})





@app.route('/like/<int:post_id>/<action>')
@login_required
def like_action(post_id, action):
	post = Post.query.filter_by(id=post_id).first_or_404()
	if action == 'like':
		current_user.like_post(post)
		db.session.commit()
	if action == 'unlike':
		current_user.unlike_post(post)
		db.session.commit()
	return redirect(request.referrer)



@app.route("/post/<int:post_id>/comment", methods=["GET", "POST"])
@login_required
def comment_post(post_id):
	post =  Post.query.filter_by(id=post_id).first_or_404()
	comment_to_show = Comment.query.filter_by(post_id=post_id).all()
	form = AddCommentForm()
	if form.validate_on_submit():
		if request.method == 'POST':
			comment = Comment(text=form.body.data, author=current_user.id, post_id=post_id)
			db.session.add(comment)
			db.session.commit()
			if post.comment_count == None:
				post.comment_count = 1
			else:
				post.comment_count += 1
			db.session.commit()	
			flash("Your comment has been added to the post", "success")
			return redirect(url_for("comment_post", post_id=post.id)) 
	return render_template("comment_dispaly.html", title="Comment Post", 
				form=form, post_id=post_id, post=post, comment_to_show=comment_to_show, comment_count=post.comment_count)




@app.route("/post/<int:post_id>")
@login_required
def delete_post(post_id):
	Post_delete = Post.query.filter_by(id=post_id).first_or_404()
	comments = Comment.query.filter_by(post_id=post_id).all()
	for i in comments:
		db.session.delete(i)
	db.session.delete(Post_delete)
	db.session.commit()
	flash("Your Post has been deleted", "success")
	return redirect(url_for('index'))		




@app.route("/update_post/<int:post_id>", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
	post = Post.query.filter_by(id=post_id).first_or_404()
	form = PostForm()
	if form.validate_on_submit():
		if request.method == 'POST':
			post.body = form.post.data
			db.session.commit()
			flash(f'Your changes have been saved.','success')
			return redirect(url_for('update_post', post_id=post.id))
	elif request.method == 'GET':
		form.post.data = post.body
	return render_template('update_post.html', post = post, form=form)	



@app.route("/delete_comment/<int:comment_id>")
@login_required
def delete_comment(comment_id):
	comment = Comment.query.filter_by(id=comment_id).first_or_404()
	Q = comment.post_id
	post = Post.query.filter_by(id=Q).first()
	post.comment_count -= 1
	db.session.delete(comment)
	db.session.commit()
	flash("Your comment has been deleted", "success")
	return redirect(url_for('comment_post', post_id=comment.post_id))




