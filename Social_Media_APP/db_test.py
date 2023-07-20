import sys

from Flask_proj import db, app
from Flask_proj.models import User, Friendship


def create_db():
    with app.app_context():
        db.create_all()

def drop_db():
    with app.app_context():
        db.drop_all()

def create_users():
    with app.app_context():
        new_user = User(first_name='Mohamed', last_name='Osama', email='Mohamed@gmail.com', password='sodium')
        db.session.add(new_user)
        db.session.commit()

def create_friendships():
    with app.app_context():
        user = User.query.first()
        friend = User.query.filter(User.id != user.id).first()
        new_friendship = Friendship(user_id=user.id, friend_id=friend.id, status='Active')
        db.session.add(new_friendship)
        db.session.commit()


def get_user():
    with app.app_context():
        user = User.query.first()
    print( user)

if __name__ == '__main__':
    globals()[sys.argv[1]]()