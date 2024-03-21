"""Message User Tests"""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.add_all([testuser, testuser2])
        db.session.commit()

        self.user_id = testuser.id
        self.user_id2 = testuser2.id

    def test_view_user(self):
        """Can we view the user?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            resp = c.get(f"/users/{self.user_id}")                    
            self.assertEqual(resp.status_code, 200)

            u = User.query.first()
            self.assertEqual(u.username, 'testuser')
            self.assertEqual(u.email, 'test@test.com')   

    def test_view_other(self):
        """Can we see another user followers when logged in"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id

            resp = c.get(f"/users/{self.user_id}")                    
            self.assertEqual(resp.status_code, 200)

            u = User.query.get(self.user_id2)
            self.assertEqual(u.username, 'testuser2')

            resp = c.get(f"/users/{self.user_id2}/following", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("col-sm-9", html)

            resp = c.get(f"/users/{self.user_id2}/followers", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("col-sm-9", html)

    def test_login_logout(self):

        # Does login succeed on valid credentials?
        u1 = User.authenticate(
            username='testuser',
            password='testuser') 
        
        d = {"username": u1.username,
            "password": "testuser"}
        resp = self.client.post("/login", data=d, follow_redirects=True)
        html = resp.get_data(as_text=True)
        
        # Does a valid login attempt work?
        self.assertEqual(resp.status_code, 200)
        self.assertIn(f"Hello, {u1.username}!", html)

        resp = self.client.get("/logout", follow_redirects=True)
        html = resp.get_data(as_text=True)

        # Does logout work?
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Goodbye!", html)


    
    def test_logged_out_view_follow(self):
        # When you’re logged out, are you disallowed from visiting a user’s follower / following pages?
        resp = self.client.get(f"/users/1/following", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized.", html)        



