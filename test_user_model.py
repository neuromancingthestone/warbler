"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['SQLALCHEMY_ECHO'] = True

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        # Does User.create successfully create a new user given valid credentials
        self.testuser1 = User.signup(
            email="test1@test.com",
            username="testuser1",
            password="cattos",
            image_url=None
        )

        db.session.commit()

        self.testuser2 = User.signup(
            email="test2@test.com",
            username="testuser2",
            password="doggos",
            image_url=None
        )        

        db.session.commit()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_login(self):
        """Can we log in?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2.id

            u = User.authenticate(
                username='testuser2',
                password='doggos')            
            self.assertEqual(u.username, 'testuser2')
            self.assertEqual(u.email, 'test2@test.com')             

    def test_following(self):
        """Does the following model work?""" 

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            # Does User.authenticate fail to return a user when the username is invalid?
            d = {"username": "testuser3",
                 "password": "doggos"}
            resp = c.post("/login", data=d, follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials.", html)

            # Does User.authenticate fail to return a user when the password is invalid?
            d = {"username": "testuser2",
                 "password": "cattos"}
            resp = c.post("/login", data=d, follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials.", html)

            # Does User.authenticate successfully return a user when given a valid username and password?
            u1 = User.authenticate(
                username='testuser1',
                password='cattos') 
            
            u2 = User.authenticate(
                username='testuser2',
                password='doggos')             

            url = f"/users/follow/{u2.id}"
            resp = c.post(url)

            self.assertEqual(resp.status_code, 302)

            # Does is_following successfully detect when user1 is following user2?
            is_following = User.is_following(u1, u2)
            self.assertEqual(is_following, 1)

            # Does is_following successfully detect when user1 is not following user2?
            is_following = User.is_following(u2, u1)
            self.assertEqual(is_following, 0)

            # Does is_followed_by successfully detect when user1 is followed by user2?
            is_followed = User.is_followed_by(u2, u1)
            self.assertEqual(is_followed, 1)

            # Does is_followed_by successfully detect when user1 is not followed by user2?
            is_followed = User.is_followed_by(u1, u2)
            self.assertEqual(is_followed, 0)         

 

