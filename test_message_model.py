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


class MessageModelTestCase(TestCase):
    """Test the model for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        self.testuser1 = User.signup(
            email="test1@test.com",
            username="testuser1",
            password="catto",
            image_url=None
        )

        db.session.commit()

        self.testuser2 = User.signup(
            email="test2@test.com",
            username="testuser2",
            password="doggo",
            image_url=None
        )     
        
        db.session.commit()           

    def test_message_model(self):
        """Does basic model work?"""

        m = Message(
            text="Test message",
            timestamp=None,
            user_id=self.testuser1.id
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.testuser1.messages), 1)
        self.assertEqual(self.testuser1.messages[0].text, "Test message")
        self.assertEqual(self.testuser1.messages[0].user_id, self.testuser1.id)

    def test_message_add(self):
        """Can we add a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            d = {"text": "Test message 2"}
            resp = c.post("/messages/new", data=d, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test message 2", html)

    def test_message_likes(self):
        """Do message likes and unlikes work?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            d = {"text": "Test message 3"}
            resp = c.post("/messages/new", data=d, follow_redirects=True)

            msg = Message.query.one()
            resp = c.post(f"/users/add_like/{msg.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("btn-primary", html)

            resp = c.post(f"/users/add_like/{msg.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("btn-secondary", html)
 


