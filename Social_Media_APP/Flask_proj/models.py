from datetime import datetime
from flask import flash
from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, ForeignKey
from Flask_proj import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    email = Column(String(255), unique=True)
    profile_image = Column(LargeBinary)
    password = Column(String(255))

    friendships = db.relationship('Friendship', foreign_keys='Friendship.user_id')
    friend_requests_sent = db.relationship('FriendRequest', foreign_keys='FriendRequest.user_id', backref='sender', lazy=True)
    friend_requests_received = db.relationship('FriendRequest', foreign_keys='FriendRequest.friend_id', backref='receiver', lazy=True)
    posts = db.relationship('Post', backref='user', lazy=True)

    def __repr__(self):
        return f"User(id={self.id}, email='{self.email}')"

    def set_profile_image(self, image_path):
        if image_path:
            with open(image_path, 'rb') as file:
                image_data = file.read()
            self.profile_image = image_data

    def send_friend_request(self, user):
        friend_request = FriendRequest(user_id=self.id, friend_id=user.id, status='pending')
        db.session.add(friend_request)
        db.session.commit()

    def has_friend_request(self, user):
        return FriendRequest.query.filter_by(user_id=self.id, friend_id=user.id, status='pending').first() is not None

    def is_friends_with(self, user):
        return Friendship.query.filter(
            (Friendship.user_id == self.id) & (Friendship.friend_id == user.id) &
            (Friendship.status == 'friends')
        ).first() is not None
    
    def get_friend_display(self, friendship):
        if friendship.user_id == self.id:
            return User.query.filter_by(id=friendship.friend_id).first()

        
    # def handle_friend_request(self, request_id, action):
    #     friend_request = FriendRequest.query.get_or_404(request_id)
    #     if action == 'accept':
    #         friends = Friendship(user_id=self.id, friend_id=friend_request.friend_id, status='friends')
    #         db.session.add(friends)
    #         db.session.delete(friend_request)
    #         db.session.commit()
    #         flash('Friend request accepted!', 'success')


class Friendship(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    friend_id = Column(Integer, ForeignKey('user.id'))
    status = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Friendship(id={self.id}, user_id={self.user_id}, friend_id={self.friend_id})"

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('sent_friend_requests', lazy=True))
    friend = db.relationship('User', foreign_keys=[friend_id], backref=db.backref('received_friend_requests', lazy=True))

    def __repr__(self):
        return f"FriendRequest(id={self.id}, user_id={self.user_id}, friend_id={self.friend_id})"



class Post(db.Model):
    post_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    content = Column(String(255))
    privacy = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Post(post_id={self.post_id}, user_id={self.user_id})"

class Chat(db.Model):
    chat_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    friend_id = Column(Integer, ForeignKey('user.id'))
    message_content = Column(String(255))
    sent_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Chat(chat_id={self.chat_id}, user_id={self.user_id}, friend_id={self.friend_id})"
