from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Message, Notification, MessageHistory


class MessageSignalTestCase(TestCase):
    """
    Test cases for Message signals and Notification creation.
    """

    def setUp(self):
        """
        Set up test users for messaging tests.
        """
        self.sender = User.objects.create_user(
            username='sender_user',
            email='sender@example.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver_user',
            email='receiver@example.com',
            password='testpass123'
        )

    def test_message_creation(self):
        """
        Test that a message can be created successfully.
        """
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Hello, this is a test message!'
        )
        
        self.assertIsNotNone(message.message_id)
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)
        self.assertEqual(message.content, 'Hello, this is a test message!')
        self.assertIsNotNone(message.timestamp)
        self.assertFalse(message.edited)

    def test_notification_created_on_message_save(self):
        """
        Test that a notification is automatically created when a message is saved.
        """
        # Check initial notification count
        initial_notification_count = Notification.objects.count()
        
        # Create a new message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Test message for notification'
        )
        
        # Check that notification count increased by 1
        self.assertEqual(Notification.objects.count(), initial_notification_count + 1)
        
        # Verify the notification was created for the receiver
        notification = Notification.objects.get(message=message)
        self.assertEqual(notification.user, self.receiver)
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.notification_type, 'message')
        self.assertIn(self.sender.username, notification.content)
        self.assertFalse(notification.is_read)

    def test_multiple_messages_create_multiple_notifications(self):
        """
        Test that multiple messages create multiple notifications.
        """
        initial_count = Notification.objects.count()
        
        # Create multiple messages
        for i in range(3):
            Message.objects.create(
                sender=self.sender,
                receiver=self.receiver,
                content=f'Test message {i+1}'
            )
        
        # Check that 3 new notifications were created
        self.assertEqual(Notification.objects.count(), initial_count + 3)
        
        # Verify all notifications are for the receiver
        receiver_notifications = Notification.objects.filter(user=self.receiver)
        self.assertEqual(receiver_notifications.count(), 3)

    def test_notification_not_created_on_message_update(self):
        """
        Test that updating a message doesn't create a new notification.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Original message'
        )
        
        # Get notification count after creation
        notification_count_after_creation = Notification.objects.count()
        
        # Update the message
        message.content = 'Updated message'
        message.save()
        
        # Verify no new notification was created
        self.assertEqual(Notification.objects.count(), notification_count_after_creation)

    def test_notification_content(self):
        """
        Test that notification content is formatted correctly.
        """
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Testing notification content'
        )
        
        notification = Notification.objects.get(message=message)
        expected_content = f"You have a new message from {self.sender.username}"
        self.assertEqual(notification.content, expected_content)

    def test_mark_notification_as_read(self):
        """
        Test the mark_as_read method on Notification model.
        """
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Test message'
        )
        
        notification = Notification.objects.get(message=message)
        self.assertFalse(notification.is_read)
        
        # Mark as read
        notification.mark_as_read()
        notification.refresh_from_db()
        
        self.assertTrue(notification.is_read)

    def test_multiple_receivers_different_notifications(self):
        """
        Test that different receivers receive separate notifications.
        """
        receiver2 = User.objects.create_user(
            username='receiver2_user',
            email='receiver2@example.com',
            password='testpass123'
        )
        
        # Send message to first receiver
        message1 = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Message to receiver 1'
        )
        
        # Send message to second receiver
        message2 = Message.objects.create(
            sender=self.sender,
            receiver=receiver2,
            content='Message to receiver 2'
        )
        
        # Check notifications
        notification1 = Notification.objects.get(message=message1)
        notification2 = Notification.objects.get(message=message2)
        
        self.assertEqual(notification1.user, self.receiver)
        self.assertEqual(notification2.user, receiver2)
        self.assertNotEqual(notification1.notification_id, notification2.notification_id)

    def test_message_string_representation(self):
        """
        Test the __str__ method of Message model.
        """
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Test message'
        )
        
        expected_str = f"Message from {self.sender.username} to {self.receiver.username} at {message.timestamp}"
        self.assertEqual(str(message), expected_str)

    def test_notification_string_representation(self):
        """
        Test the __str__ method of Notification model.
        """
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Test message'
        )
        
        notification = Notification.objects.get(message=message)
        expected_str = f"Notification for {self.receiver.username}: {notification.content[:50]}"
        self.assertEqual(str(notification), expected_str)


class MessageEditSignalTestCase(TestCase):
    """
    Test cases for Message edit signals and MessageHistory creation.
    """

    def setUp(self):
        """
        Set up test users and message for edit tests.
        """
        self.sender = User.objects.create_user(
            username='sender_user',
            email='sender@example.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver_user',
            email='receiver@example.com',
            password='testpass123'
        )

    def test_message_edit_creates_history(self):
        """
        Test that editing a message creates a history entry.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Original content'
        )
        
        # Verify no history exists yet
        self.assertEqual(MessageHistory.objects.count(), 0)
        self.assertFalse(message.edited)
        
        # Edit the message
        message.content = 'Updated content'
        message.save()
        
        # Refresh from database
        message.refresh_from_db()
        
        # Verify history was created
        self.assertEqual(MessageHistory.objects.count(), 1)
        self.assertTrue(message.edited)
        self.assertIsNotNone(message.last_edited_at)
        
        # Verify history content
        history = MessageHistory.objects.first()
        self.assertEqual(history.message, message)
        self.assertEqual(history.old_content, 'Original content')
        self.assertEqual(history.edited_by, self.sender)

    def test_multiple_edits_create_multiple_history_entries(self):
        """
        Test that multiple edits create multiple history entries.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Version 1'
        )
        
        # First edit
        message.content = 'Version 2'
        message.save()
        
        # Second edit
        message.content = 'Version 3'
        message.save()
        
        # Third edit
        message.content = 'Version 4'
        message.save()
        
        # Verify 3 history entries were created
        self.assertEqual(MessageHistory.objects.filter(message=message).count(), 3)
        
        # Verify history entries have correct old content
        histories = MessageHistory.objects.filter(message=message).order_by('edited_at')
        self.assertEqual(histories[0].old_content, 'Version 1')
        self.assertEqual(histories[1].old_content, 'Version 2')
        self.assertEqual(histories[2].old_content, 'Version 3')

    def test_no_history_created_when_content_unchanged(self):
        """
        Test that no history is created when message is saved without content change.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Original content'
        )
        
        # Save without changing content
        message.save()
        
        # Verify no history was created
        self.assertEqual(MessageHistory.objects.count(), 0)
        self.assertFalse(message.edited)

    def test_message_edited_flag(self):
        """
        Test that the edited flag is set correctly.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Original content'
        )
        
        self.assertFalse(message.edited)
        self.assertIsNone(message.last_edited_at)
        
        # Edit the message
        message.content = 'Edited content'
        message.save()
        message.refresh_from_db()
        
        self.assertTrue(message.edited)
        self.assertIsNotNone(message.last_edited_at)

    def test_message_history_string_representation(self):
        """
        Test the __str__ method of MessageHistory model.
        """
        # Create and edit a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Original content'
        )
        
        message.content = 'Updated content'
        message.save()
        
        # Get the history entry
        history = MessageHistory.objects.first()
        expected_str = f"History for message {message.message_id} edited at {history.edited_at}"
        self.assertEqual(str(history), expected_str)

    def test_message_history_relationship(self):
        """
        Test that message history is accessible through the message relationship.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Version 1'
        )
        
        # Edit multiple times
        message.content = 'Version 2'
        message.save()
        
        message.content = 'Version 3'
        message.save()
        
        # Access history through message relationship
        history_entries = message.history.all()
        self.assertEqual(history_entries.count(), 2)

    def test_new_message_has_no_history(self):
        """
        Test that creating a new message doesn't create history.
        """
        initial_history_count = MessageHistory.objects.count()
        
        # Create a new message
        Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='New message'
        )
        
        # Verify no history was created
        self.assertEqual(MessageHistory.objects.count(), initial_history_count)


class UserDeletionSignalTestCase(TestCase):
    """
    Test cases for User deletion signals and cleanup of related data.
    """

    def setUp(self):
        """
        Set up test users and data for deletion tests.
        """
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )

    def test_user_deletion_removes_sent_messages(self):
        """
        Test that deleting a user removes all messages they sent.
        """
        # Create messages sent by user1
        message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Message from user1 to user2'
        )
        message2 = Message.objects.create(
            sender=self.user1,
            receiver=self.user3,
            content='Message from user1 to user3'
        )
        
        # Verify messages exist
        self.assertEqual(Message.objects.filter(sender=self.user1).count(), 2)
        
        # Delete user1
        self.user1.delete()
        
        # Verify messages were deleted
        self.assertEqual(Message.objects.filter(message_id=message1.message_id).count(), 0)
        self.assertEqual(Message.objects.filter(message_id=message2.message_id).count(), 0)

    def test_user_deletion_removes_received_messages(self):
        """
        Test that deleting a user removes all messages they received.
        """
        # Create messages received by user2
        message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Message to user2 from user1'
        )
        message2 = Message.objects.create(
            sender=self.user3,
            receiver=self.user2,
            content='Message to user2 from user3'
        )
        
        # Verify messages exist
        self.assertEqual(Message.objects.filter(receiver=self.user2).count(), 2)
        
        # Delete user2
        self.user2.delete()
        
        # Verify messages were deleted
        self.assertEqual(Message.objects.filter(message_id=message1.message_id).count(), 0)
        self.assertEqual(Message.objects.filter(message_id=message2.message_id).count(), 0)

    def test_user_deletion_removes_notifications(self):
        """
        Test that deleting a user removes all their notifications.
        """
        # Create messages which will create notifications
        Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Message 1'
        )
        Message.objects.create(
            sender=self.user3,
            receiver=self.user2,
            content='Message 2'
        )
        
        # Verify notifications were created
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), 2)
        
        # Delete user2
        self.user2.delete()
        
        # Verify notifications were deleted
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), 0)

    def test_user_deletion_clears_message_history_references(self):
        """
        Test that deleting a user clears edited_by references in message history.
        """
        # Create a message
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Original content'
        )
        
        # Edit the message to create history
        message.content = 'Updated content'
        message.save()
        
        # Verify history was created with edited_by
        history = MessageHistory.objects.first()
        self.assertEqual(history.edited_by, self.user1)
        
        # Delete user1
        self.user1.delete()
        
        # Since the message is deleted with user1, history should also be deleted via CASCADE
        self.assertEqual(MessageHistory.objects.count(), 0)

    def test_user_deletion_does_not_affect_other_users_data(self):
        """
        Test that deleting one user doesn't affect other users' data.
        """
        # Create messages between different users
        message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Message from user1 to user2'
        )
        message2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user3,
            content='Message from user2 to user3'
        )
        
        # Delete user1
        self.user1.delete()
        
        # Verify message1 was deleted but message2 still exists
        self.assertEqual(Message.objects.filter(message_id=message1.message_id).count(), 0)
        self.assertEqual(Message.objects.filter(message_id=message2.message_id).count(), 1)
        
        # Verify user2 and user3 still exist
        self.assertTrue(User.objects.filter(username='user2').exists())
        self.assertTrue(User.objects.filter(username='user3').exists())

    def test_cascade_deletion_of_message_history(self):
        """
        Test that message history is deleted when associated message is deleted.
        """
        # Create and edit a message
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Original content'
        )
        
        message.content = 'Updated content'
        message.save()
        
        # Verify history exists
        self.assertEqual(MessageHistory.objects.filter(message=message).count(), 1)
        
        # Delete the user (which deletes the message)
        self.user1.delete()
        
        # Verify history was also deleted (CASCADE)
        self.assertEqual(MessageHistory.objects.count(), 0)

    def test_multiple_users_deletion(self):
        """
        Test deleting multiple users cleans up all their data.
        """
        # Create messages between all users
        Message.objects.create(sender=self.user1, receiver=self.user2, content='Msg 1')
        Message.objects.create(sender=self.user2, receiver=self.user3, content='Msg 2')
        Message.objects.create(sender=self.user3, receiver=self.user1, content='Msg 3')
        
        # Verify initial counts
        self.assertEqual(Message.objects.count(), 3)
        self.assertEqual(Notification.objects.count(), 3)
        
        # Delete all users
        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        
        # Verify all messages and notifications were deleted
        self.assertEqual(Message.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)


class UserDeletionViewTestCase(TestCase):
    """
    Test cases for user deletion views.
    """

    def setUp(self):
        """
        Set up test client and users.
        """
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='testpass123'
        )

    def test_delete_user_account_view_requires_login(self):
        """
        Test that delete account view requires authentication.
        """
        response = self.client.get(reverse('messaging:delete_user_account'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_delete_user_account_view_displays_confirmation(self):
        """
        Test that delete account view displays confirmation page.
        """
        # Login
        self.client.login(username='testuser', password='testpass123')
        
        # Create some data for the user
        Message.objects.create(
            sender=self.user,
            receiver=self.other_user,
            content='Test message'
        )
        
        response = self.client.get(reverse('messaging:delete_user_account'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('sent_messages_count', response.context)

    def test_delete_user_requires_post(self):
        """
        Test that delete user endpoint only accepts POST requests.
        """
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('messaging:delete_user'))
        # Should return 405 Method Not Allowed or redirect
        self.assertIn(response.status_code, [302, 405])

    def test_delete_user_with_confirmation(self):
        """
        Test successful user deletion with proper confirmation.
        """
        self.client.login(username='testuser', password='testpass123')
        
        # Create some data
        Message.objects.create(
            sender=self.user,
            receiver=self.other_user,
            content='Test message'
        )
        
        # Verify user exists
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        # Delete user with confirmation
        response = self.client.post(
            reverse('messaging:delete_user'),
            {'confirmation': 'delete'}
        )
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Verify user was deleted
        self.assertFalse(User.objects.filter(username='testuser').exists())

    def test_delete_user_without_proper_confirmation(self):
        """
        Test that deletion fails without proper confirmation.
        """
        self.client.login(username='testuser', password='testpass123')
        
        # Try to delete without proper confirmation
        response = self.client.post(
            reverse('messaging:delete_user'),
            {'confirmation': 'wrong'}
        )
        
        # Should redirect back
        self.assertEqual(response.status_code, 302)
        
        # Verify user still exists
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_user_data_summary_api(self):
        """
        Test user data summary API endpoint.
        """
        self.client.login(username='testuser', password='testpass123')
        
        # Create some data
        Message.objects.create(
            sender=self.user,
            receiver=self.other_user,
            content='Test message 1'
        )
        Message.objects.create(
            sender=self.other_user,
            receiver=self.user,
            content='Test message 2'
        )
        
        response = self.client.get(reverse('messaging:user_data_summary'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['sent_messages_count'], 1)
        self.assertEqual(data['received_messages_count'], 1)
        self.assertEqual(data['notifications_count'], 1)  # One notification for received message


class ThreadedConversationTestCase(TestCase):
    """
    Test cases for threaded conversation functionality and ORM optimizations.
    """

    def setUp(self):
        """
        Set up test users for threading tests.
        """
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )

    def test_message_with_parent_is_reply(self):
        """
        Test that a message with a parent is identified as a reply.
        """
        # Create root message
        root_message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root message'
        )
        
        # Create reply
        reply = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply to root',
            parent_message=root_message
        )
        
        self.assertTrue(reply.is_reply())
        self.assertFalse(root_message.is_reply())

    def test_get_thread_root(self):
        """
        Test getting the root message of a conversation thread.
        """
        # Create message hierarchy: root -> reply1 -> reply2
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        reply1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply 1',
            parent_message=root
        )
        
        reply2 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Reply 2',
            parent_message=reply1
        )
        
        # All messages should return same root
        self.assertEqual(root.get_thread_root(), root)
        self.assertEqual(reply1.get_thread_root(), root)
        self.assertEqual(reply2.get_thread_root(), root)

    def test_get_all_replies(self):
        """
        Test retrieving all direct replies to a message.
        """
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        # Create 3 direct replies
        reply1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply 1',
            parent_message=root
        )
        
        reply2 = Message.objects.create(
            sender=self.user3,
            receiver=self.user1,
            content='Reply 2',
            parent_message=root
        )
        
        reply3 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply 3',
            parent_message=root
        )
        
        replies = root.get_all_replies()
        self.assertEqual(replies.count(), 3)

    def test_get_reply_count(self):
        """
        Test getting the count of direct replies.
        """
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        self.assertEqual(root.get_reply_count(), 0)
        
        # Add replies
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply 1',
            parent_message=root
        )
        
        Message.objects.create(
            sender=self.user3,
            receiver=self.user1,
            content='Reply 2',
            parent_message=root
        )
        
        self.assertEqual(root.get_reply_count(), 2)

    def test_get_total_reply_count_nested(self):
        """
        Test getting total count of all nested replies.
        """
        # Create nested structure: root -> reply1 -> reply2 -> reply3
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        reply1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply 1',
            parent_message=root
        )
        
        reply2 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Reply 2',
            parent_message=reply1
        )
        
        reply3 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply 3',
            parent_message=reply2
        )
        
        # Root should have 3 total replies
        self.assertEqual(root.get_total_reply_count(), 3)
        # reply1 should have 2 nested replies
        self.assertEqual(reply1.get_total_reply_count(), 2)
        # reply2 should have 1 nested reply
        self.assertEqual(reply2.get_total_reply_count(), 1)

    def test_get_thread_messages(self):
        """
        Test getting all messages in a thread.
        """
        # Create thread structure
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        reply1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply 1',
            parent_message=root
        )
        
        reply2 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Reply 2',
            parent_message=reply1
        )
        
        # Get all thread messages from any message in thread
        thread_messages = reply2.get_thread_messages()
        
        # Should include root and all replies
        self.assertGreaterEqual(thread_messages.count(), 3)

    def test_get_conversation_participants(self):
        """
        Test getting all participants in a conversation thread.
        """
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply 1',
            parent_message=root
        )
        
        Message.objects.create(
            sender=self.user3,
            receiver=self.user2,
            content='Reply 2',
            parent_message=root
        )
        
        participants = root.get_conversation_participants()
        
        # Should include all 3 users
        self.assertEqual(len(participants), 3)
        self.assertIn(self.user1, participants)
        self.assertIn(self.user2, participants)
        self.assertIn(self.user3, participants)

    def test_get_root_messages_optimized(self):
        """
        Test getting root messages with optimized queries.
        """
        # Create root messages
        root1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root 1'
        )
        
        root2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user3,
            content='Root 2'
        )
        
        # Create replies (should not be in root messages)
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply to root 1',
            parent_message=root1
        )
        
        root_messages = Message.get_root_messages_optimized()
        
        # Should only return root messages, not replies
        self.assertEqual(root_messages.count(), 2)

    def test_conversation_tree_structure(self):
        """
        Test building a conversation tree structure.
        """
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        reply1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply 1',
            parent_message=root
        )
        
        reply2 = Message.objects.create(
            sender=self.user3,
            receiver=self.user1,
            content='Reply 2',
            parent_message=root
        )
        
        nested_reply = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Nested reply',
            parent_message=reply1
        )
        
        tree = Message.get_conversation_tree(root)
        
        # Verify tree structure
        self.assertEqual(tree['message'], root)
        self.assertEqual(len(tree['replies']), 2)
        self.assertEqual(tree['replies'][0]['message'], reply1)
        self.assertEqual(len(tree['replies'][0]['replies']), 1)
        self.assertEqual(tree['replies'][0]['replies'][0]['message'], nested_reply)

    def test_reply_notification_type(self):
        """
        Test that replies create 'reply' type notifications.
        """
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        # Clear existing notifications
        Notification.objects.all().delete()
        
        # Create reply
        reply = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply',
            parent_message=root
        )
        
        # Check notification type
        notification = Notification.objects.filter(user=self.user1).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.notification_type, 'reply')

    def test_cascade_delete_with_replies(self):
        """
        Test that deleting a parent message cascades to replies.
        """
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        reply = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply',
            parent_message=root
        )
        
        reply_id = reply.message_id
        
        # Delete root message
        root.delete()
        
        # Reply should also be deleted (CASCADE)
        self.assertFalse(Message.objects.filter(message_id=reply_id).exists())

    def test_complex_threaded_conversation(self):
        """
        Test a complex multi-level threaded conversation.
        """
        # Create structure:
        # root
        #   ├── reply1
        #   │   └── reply1_1
        #   └── reply2
        #       ├── reply2_1
        #       └── reply2_2
        
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        reply1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply 1',
            parent_message=root
        )
        
        reply1_1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Reply 1.1',
            parent_message=reply1
        )
        
        reply2 = Message.objects.create(
            sender=self.user3,
            receiver=self.user1,
            content='Reply 2',
            parent_message=root
        )
        
        reply2_1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user3,
            content='Reply 2.1',
            parent_message=reply2
        )
        
        reply2_2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user3,
            content='Reply 2.2',
            parent_message=reply2
        )
        
        # Verify counts
        self.assertEqual(root.get_reply_count(), 2)  # Direct replies
        self.assertEqual(root.get_total_reply_count(), 5)  # All nested
        self.assertEqual(reply1.get_total_reply_count(), 1)
        self.assertEqual(reply2.get_total_reply_count(), 2)

    def test_orm_optimization_select_related(self):
        """
        Test that select_related reduces database queries.
        """
        # Create messages
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply',
            parent_message=root
        )
        
        # Query with select_related should minimize queries
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        
        with CaptureQueriesContext(connection) as context:
            messages = Message.objects.select_related(
                'sender', 'receiver', 'parent_message'
            ).filter(parent_message=root)
            
            # Access related objects
            for msg in messages:
                _ = msg.sender.username
                _ = msg.receiver.username
                if msg.parent_message:
                    _ = msg.parent_message.content
            
            # Should use fewer queries than without select_related
            query_count = len(context.captured_queries)
            self.assertLess(query_count, 5)

    def test_orm_optimization_prefetch_related(self):
        """
        Test that prefetch_related optimizes reverse relations.
        """
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        # Create multiple replies
        for i in range(5):
            Message.objects.create(
                sender=self.user2,
                receiver=self.user1,
                content=f'Reply {i}',
                parent_message=root
            )
        
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        
        with CaptureQueriesContext(connection) as context:
            # Query with prefetch_related
            roots = Message.objects.filter(
                message_id=root.message_id
            ).prefetch_related('replies')
            
            # Access replies
            for root_msg in roots:
                replies = list(root_msg.replies.all())
            
            query_count = len(context.captured_queries)
            # Should use only 2 queries (1 for root, 1 for replies)
            self.assertLessEqual(query_count, 3)


class ThreadedConversationViewTestCase(TestCase):
    """
    Test cases for threaded conversation views.
    """

    def setUp(self):
        """
        Set up test client and users.
        """
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

    def test_conversation_thread_view(self):
        """
        Test conversation thread view displays correctly.
        """
        self.client.login(username='user1', password='testpass123')
        
        # Create threaded conversation
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        reply = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply',
            parent_message=root
        )
        
        response = self.client.get(
            reverse('messaging:conversation_thread', args=[reply.message_id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('conversation_tree', response.context)
        self.assertIn('root_message', response.context)

    def test_create_reply_view(self):
        """
        Test creating a reply via view.
        """
        self.client.login(username='user1', password='testpass123')
        
        root = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Root message'
        )
        
        initial_reply_count = root.get_reply_count()
        
        response = self.client.post(
            reverse('messaging:create_reply', args=[root.message_id]),
            {'content': 'My reply'}
        )
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Verify reply was created
        root.refresh_from_db()
        self.assertEqual(root.get_reply_count(), initial_reply_count + 1)

    def test_conversation_tree_json_api(self):
        """
        Test conversation tree JSON API endpoint.
        """
        self.client.login(username='user1', password='testpass123')
        
        root = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root'
        )
        
        reply = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply',
            parent_message=root
        )
        
        response = self.client.get(
            reverse('messaging:conversation_tree_json', args=[root.message_id])
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['content'], 'Root')
        self.assertEqual(len(data['replies']), 1)
        self.assertEqual(data['replies'][0]['content'], 'Reply')


class UnreadMessagesManagerTestCase(TestCase):
    """
    Test cases for custom UnreadMessagesManager.
    """

    def setUp(self):
        """
        Set up test users for unread message tests.
        """
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )

    def test_unread_for_user(self):
        """
        Test getting unread messages for a specific user.
        """
        # Create messages
        msg1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Message 1'
        )
        
        msg2 = Message.objects.create(
            sender=self.user3,
            receiver=self.user2,
            content='Message 2'
        )
        
        msg3 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Message 3',
            read=True
        )
        
        # Get unread messages for user2
        unread = Message.unread.unread_for_user(self.user2)
        
        self.assertEqual(unread.count(), 2)
        self.assertIn(msg1, unread)
        self.assertIn(msg2, unread)
        self.assertNotIn(msg3, unread)

    def test_unread_count_for_user(self):
        """
        Test getting count of unread messages.
        """
        # Initially no unread messages
        self.assertEqual(Message.unread.unread_count_for_user(self.user2), 0)
        
        # Create unread messages
        Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Unread 1'
        )
        
        Message.objects.create(
            sender=self.user3,
            receiver=self.user2,
            content='Unread 2'
        )
        
        # Create read message
        Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Read message',
            read=True
        )
        
        # Check count
        self.assertEqual(Message.unread.unread_count_for_user(self.user2), 2)

    def test_unread_by_sender(self):
        """
        Test getting unread messages from specific sender.
        """
        # Create messages from different senders
        msg1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='From user1'
        )
        
        Message.objects.create(
            sender=self.user3,
            receiver=self.user2,
            content='From user3'
        )
        
        msg3 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='From user1 again'
        )
        
        # Get unread from user1 only
        unread_from_user1 = Message.unread.unread_by_sender(self.user2, self.user1)
        
        self.assertEqual(unread_from_user1.count(), 2)
        self.assertIn(msg1, unread_from_user1)
        self.assertIn(msg3, unread_from_user1)

    def test_mark_all_read_for_user(self):
        """
        Test marking all messages as read for a user.
        """
        # Create unread messages
        Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Unread 1'
        )
        
        Message.objects.create(
            sender=self.user3,
            receiver=self.user2,
            content='Unread 2'
        )
        
        # Verify unread count
        self.assertEqual(Message.unread.unread_count_for_user(self.user2), 2)
        
        # Mark all as read
        count = Message.unread.mark_all_read_for_user(self.user2)
        
        self.assertEqual(count, 2)
        self.assertEqual(Message.unread.unread_count_for_user(self.user2), 0)

    def test_unread_threads_for_user(self):
        """
        Test getting unread root messages (threads).
        """
        # Create root messages
        root1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Root 1'
        )
        
        root2 = Message.objects.create(
            sender=self.user3,
            receiver=self.user2,
            content='Root 2',
            read=True
        )
        
        # Create reply (should not be in unread threads)
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Reply to root 1',
            parent_message=root1
        )
        
        # Get unread threads
        unread_threads = Message.unread.unread_threads_for_user(self.user2)
        
        self.assertEqual(unread_threads.count(), 1)
        self.assertIn(root1, unread_threads)
        self.assertNotIn(root2, unread_threads)

    def test_mark_as_read_method(self):
        """
        Test the mark_as_read instance method.
        """
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Test message'
        )
        
        self.assertFalse(message.read)
        
        message.mark_as_read()
        message.refresh_from_db()
        
        self.assertTrue(message.read)

    def test_mark_as_unread_method(self):
        """
        Test the mark_as_unread instance method.
        """
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Test message',
            read=True
        )
        
        self.assertTrue(message.read)
        
        message.mark_as_unread()
        message.refresh_from_db()
        
        self.assertFalse(message.read)

    def test_default_manager_still_works(self):
        """
        Test that the default manager still works alongside custom manager.
        """
        Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Test'
        )
        
        # Both managers should work
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Message.unread.unread_count_for_user(self.user2), 1)

    def test_unread_messages_only_for_receiver(self):
        """
        Test that unread messages are only counted for receiver, not sender.
        """
        Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Test'
        )
        
        # user1 sent the message, should have 0 unread
        self.assertEqual(Message.unread.unread_count_for_user(self.user1), 0)
        
        # user2 received the message, should have 1 unread
        self.assertEqual(Message.unread.unread_count_for_user(self.user2), 1)

    def test_orm_optimization_with_only(self):
        """
        Test that .only() optimization works with custom manager.
        """
        Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Test message'
        )
        
        # Query with .only()
        unread = Message.unread.unread_for_user(self.user2).only(
            'message_id',
            'content',
            'timestamp'
        )
        
        self.assertEqual(unread.count(), 1)
        message = unread.first()
        
        # These fields should be accessible
        self.assertIsNotNone(message.message_id)
        self.assertIsNotNone(message.content)
        self.assertIsNotNone(message.timestamp)


class UnreadMessagesViewTestCase(TestCase):
    """
    Test cases for unread messages views.
    """

    def setUp(self):
        """
        Set up test client and users.
        """
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

    def test_unread_messages_view(self):
        """
        Test unread messages view displays correctly.
        """
        self.client.login(username='user1', password='testpass123')
        
        # Create unread message
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Unread message'
        )
        
        response = self.client.get(reverse('messaging:unread_messages'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('unread_messages', response.context)
        self.assertEqual(response.context['unread_count'], 1)

    def test_mark_message_read_view(self):
        """
        Test marking a message as read via view.
        """
        self.client.login(username='user1', password='testpass123')
        
        message = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Test message'
        )
        
        self.assertFalse(message.read)
        
        response = self.client.get(
            reverse('messaging:mark_message_read', args=[message.message_id])
        )
        
        message.refresh_from_db()
        self.assertTrue(message.read)

    def test_mark_all_read_view(self):
        """
        Test marking all messages as read via view.
        """
        self.client.login(username='user1', password='testpass123')
        
        # Create multiple unread messages
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Message 1'
        )
        
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Message 2'
        )
        
        self.assertEqual(Message.unread.unread_count_for_user(self.user1), 2)
        
        response = self.client.get(reverse('messaging:mark_all_read'))
        
        self.assertEqual(Message.unread.unread_count_for_user(self.user1), 0)

    def test_unread_by_sender_view(self):
        """
        Test viewing unread messages from specific sender.
        """
        self.client.login(username='user1', password='testpass123')
        
        # Create messages from user2
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='From user2'
        )
        
        response = self.client.get(
            reverse('messaging:unread_by_sender', args=['user2'])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('unread_messages', response.context)
        self.assertEqual(response.context['sender'], self.user2)

    def test_inbox_view(self):
        """
        Test inbox view with unread count.
        """
        self.client.login(username='user1', password='testpass123')
        
        # Create messages
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Unread'
        )
        
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Read',
            read=True
        )
        
        response = self.client.get(reverse('messaging:inbox'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['unread_count'], 1)
        self.assertEqual(response.context['received_messages'].count(), 2)

    def test_unread_count_api(self):
        """
        Test unread count API endpoint.
        """
        self.client.login(username='user1', password='testpass123')
        
        # Create unread messages
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Unread 1'
        )
        
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Unread 2'
        )
        
        response = self.client.get(reverse('messaging:unread_count_api'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['unread_count'], 2)

    def test_unread_messages_requires_login(self):
        """
        Test that unread messages view requires authentication.
        """
        response = self.client.get(reverse('messaging:unread_messages'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
