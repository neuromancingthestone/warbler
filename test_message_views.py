"""Message View tests."""

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


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_logged_in_messaging(self):
        # Does login succeed on valid credentials?
        u1 = User.authenticate(
            username='testuser',
            password='testuser') 
                
        d = {"username": u1.username,
            "password": "testuser"}
        resp = self.client.post("/login", data=d, follow_redirects=True)
        html = resp.get_data(as_text=True)
        
        # Make sure login works
        self.assertEqual(resp.status_code, 200)
        self.assertIn(f"Hello, {u1.username}!", html) 

        # When you’re logged in, can you add a message as yourself?               
        test_message = "Test message 1"
        d = {
            "text": test_message
            }
        resp = self.client.post("/messages/new", data=d, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(test_message, html)

        # Can you get that message from the db?
        msg = Message.query.first()
        self.assertEqual(msg.text, test_message)

        # Can you delete that message?
        resp = self.client.post(f"messages/{msg.id}/delete", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Message deleted!", html)

    def test_logged_out_messaging(self):
        # When you’re logged out, are you prohibited from adding messages?        
        d = {
            "text": "Test message",
            "timestamp": None,
            "user_id": 1
            }
        resp = self.client.post("/messages/new", data=d, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized.", html)    
        
        # When you’re logged out, are you prohibited from deleting messages?
        resp = self.client.post("/messages/1/delete", follow_redirects=True)        
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized.", html)        