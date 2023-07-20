import base64

from flask import render_template, redirect, url_for, flash, request, Blueprint
from sqlalchemy import and_, desc, or_
from werkzeug.utils import secure_filename
from Flask_proj import app, db, bcrypt
from Flask_proj.forms import RegistrationForm, LoginForm, PostForm, FriendRequestForm, ChatForm, EditProfileForm
from Flask_proj.models import User, Friendship, FriendRequest, Post, Chat
from flask_login import current_user, login_user, logout_user, login_required
import os

UPLOAD_FOLDER = 'static/images/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
users = Blueprint(
    'users',
    __name__,
    url_prefix='/users'
)

def allowed_image(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# Authentication
# --------------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if 'profile_picture' in request.files:
            profile_picture = request.files['profile_picture']
            if profile_picture.filename != '' and allowed_image(profile_picture.filename):
                filename = secure_filename(profile_picture.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                profile_image = open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb').read()
            else:
                flash('Invalid file type. Please upload a valid image file.', 'error')
                return redirect(url_for('register'))
        else:
            profile_image = b''

        user = User(first_name=first_name, last_name=last_name, email=email,
                    profile_image=profile_image, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid email or password. Please try again.', 'error')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))




#     return render_template('home.html', form=form, posts=posts, friend_requests=friend_requests, privacy_mode=privacy_mode)
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    friend_requests = FriendRequest.query.filter_by(friend_id=current_user.id).all()
    form = PostForm()
    privacy_mode = request.args.get('privacy_mode', 'all')  # Get the privacy mode from the query parameter

    if form.validate_on_submit():
        content = form.content.data
        privacy = form.privacy.data
        post = Post(user_id=current_user.id, content=content, privacy=privacy)
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('home', privacy_mode=privacy_mode))
    
    user_ids = [friendship.user_id for friendship in current_user.friendships]
    friend_ids = [friendship.friend_id for friendship in current_user.friendships]
    if privacy_mode == 'all':
        # Fetch public posts, posts of friends with privacy set to "Public," and posts of the current user
        posts = Post.query.filter(
            or_(
                (Post.privacy == 'Public'),
                and_(
                    (Post.privacy == 'Friends'),
                    # (Post.user_id.in_(friend_ids))
                    or_(
                    (Post.user_id.in_(friend_ids)),
                    (Post.user_id.in_(user_ids))
                    )
                ),
                and_(
                    (Post.privacy == 'Only Me'),
                    (Post.user_id == current_user.id)
                )
            )
        ).order_by(desc(Post.created_at))

    elif privacy_mode == 'friends':
        # Fetch posts of friends with privacy set to "Public" or "Friends"
        posts = Post.query.filter(
            or_(
            Post.user_id.in_(friend_ids),
            Post.user_id.in_(user_ids)
            ),
            or_(
            Post.privacy == 'Public',
            Post.privacy == 'Friends'
            )
        ).order_by(desc(Post.created_at)).all()


    else:
        # Fetch public posts and posts of the current user
        posts = Post.query.filter(
            or_(
                (Post.privacy == 'Public'),
                (Post.privacy == 'Only Me' and Post.user_id == current_user.id)
            )
        ).order_by(desc(Post.created_at))
    return render_template('home.html', form=form, posts=posts, friend_requests=friend_requests, privacy_mode=privacy_mode)



@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)

    if user_id == current_user.id:
        posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc())
    elif Friendship.query.filter_by(user_id=current_user.id, friend_id=user_id).first():
        posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc())
    else:
        posts = Post.query.filter_by(user_id=user_id, privacy='Public').order_by(Post.created_at.desc())

    return render_template('profile.html', user=user, posts=posts, base64=base64)


@app.template_filter('b64encode')
def b64encode_filter(data):
    return base64.b64encode(data).decode('utf-8')

# Flask route
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(obj=current_user)  # Load form with current user data

    if form.validate_on_submit():
        form.populate_obj(current_user)  # Update current user object with form data
        if form.profile_picture.data:
            # Process profile picture upload if provided
            profile_picture = form.profile_picture.data
            if profile_picture.filename != '' and allowed_image(profile_picture.filename):
                filename = secure_filename(profile_picture.filename)
                profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_image = open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb').read()
            else:
                flash('Invalid file type. Please upload a valid image file.', 'error')
                return redirect(url_for('edit_profile'))
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', user_id=current_user.id))

    return render_template('edit_profile.html', form=form)


@users.route('/<int:user_id>', methods=['GET'])
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)


# Friends & Friend Requests
# --------------------------------------------------------------------------

@app.route('/send_friend_request/<int:user_id>', methods=['POST'])
@login_required
def send_friend_request(user_id):
    user = User.query.get(user_id)
    if user and not current_user.is_friends_with(user):
        friend_request = FriendRequest.query.filter_by(user_id=current_user.id, friend_id=user.id, status='pending').first()
        if not friend_request:
            friend_request = FriendRequest(user_id=current_user.id, friend_id=user.id, status='pending')
            db.session.add(friend_request)
            db.session.commit()
    return redirect(url_for('profile', user_id=user_id))


@app.route('/cancel_friend_request/<int:request_id>', methods=['POST'])
@login_required
def cancel_friend_request(request_id):
    friend_request = FriendRequest.query.get(request_id)
    if friend_request:
        db.session.delete(friend_request)
        db.session.commit()
        return redirect(url_for('profile', user_id=friend_request.friend_id))
    return redirect(request.referrer)
 

@app.route('/friend_requests', methods=['GET', 'POST'])
@login_required
def friend_requests():
    friend_requests_received = FriendRequest.query.filter_by(friend_id=current_user.id, status='pending').all()
    users = User.query.filter(User.id != current_user.id).all()
    
    print(users)
    return render_template('friend_requests.html', friend_requests=friend_requests_received, users = users)


@app.route('/handle_friend_request/<int:request_id>/<action>', methods=['POST'])
@login_required
def handle_friend_request( request_id, action):
    friend_request = FriendRequest.query.get_or_404(request_id)
    if action == 'accept':
        friends = Friendship(user_id=friend_request.user_id, friend_id=friend_request.friend_id, status='friends')
        friend_user_first = Friendship(user_id=friend_request.friend_id, friend_id=friend_request.user_id, status='friends')
        db.session.add(friends)
        db.session.add(friend_user_first)
        db.session.delete(friend_request)
        db.session.commit()
        flash('Friend request accepted!', 'success')

    if action == 'decline':
        db.session.delete(friend_request)
        db.session.commit()
        flash('Friend request Decline!', 'success')
    return redirect(request.referrer)

@app.route('/remove_friend/<int:user_id>/<int:friend_id>', methods=['POST'])
@login_required
def remove_friend(user_id, friend_id):
    with app.app_context():
        friendship = Friendship.query.filter_by(user_id=user_id, friend_id=friend_id).first()
        friendship_reverse = Friendship.query.filter_by(user_id=friend_id, friend_id=user_id).first()
        if friendship:
            db.session.delete(friendship)
        if friendship_reverse:
            db.session.delete(friendship_reverse)

        db.session.commit()
    return redirect(request.referrer)


# Posts Operations
# --------------------------------------------------------------------------


@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        content = form.content.data
        privacy = form.privacy.data

        # Create a new post object and save it to the database
        post = Post(user_id=current_user.id, content=content, privacy=privacy)
        db.session.add(post)
        db.session.commit()

        flash('Post created successfully!', 'success')
        return redirect(url_for('home'))

@app.route('/delete_post/<int:post_id>', methods=['Get','POST'])
@login_required
def delete_post(post_id):
    with app.app_context():
        post = Post.query.get_or_404(post_id)
        if (not post) or (not post.user_id == current_user.id):
            print(post)
            print(post.user_id == current_user.id)
            return redirect(request.referrer)
        if post.user_id != current_user.id:
            flash('You do not have permission to delete this post.', 'error')
        else:
            db.session.delete(post)
            db.session.commit()
            flash('Post deleted successfully!', 'success')
    return redirect(request.referrer)


@app.route('/update_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        flash('You do not have permission to update this post.', 'error')
        return redirect(url_for('home'))

    form = PostForm(obj = post)
    if form.validate_on_submit():
        post.content = form.content.data
        post.privacy = form.privacy.data
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('profile',user_id=current_user.id ))
    elif request.method == 'GET':
        form.content.data = post.content
        form.privacy.data = post.privacy
    return render_template('update_post.html', form=form)