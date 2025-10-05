import uuid
from django.db import models
from django.contrib.auth.models import User
from managers import UnreadMessagesManager


class Message(models.Model):
    """
    Message model for storing user messages with threading support.
    """
    message_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        db_column='sender_id'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
        db_column='recipient_id'
    )
    content = models.TextField(null=False, blank=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    edited = models.BooleanField(default=False)
    last_edited_at = models.DateTimeField(null=True, blank=True)
    read = models.BooleanField(default=False, db_index=True)
    
    # Self-referential foreign key for threaded conversations
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        db_index=True
    )
    
    # Default manager
    objects = models.Manager()
    
    # Custom manager for unread messages
    unread = UnreadMessagesManager()

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['parent_message', '-timestamp']),
            models.Index(fields=['receiver', 'read', '-timestamp']),
        ]

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username} at {self.timestamp}"

    def mark_as_read(self):
        """Mark this message as read."""
        if not self.read:
            self.read = True
            self.save(update_fields=['read'])
    
    def mark_as_unread(self):
        """Mark this message as unread."""
        if self.read:
            self.read = False
            self.save(update_fields=['read'])

    def is_reply(self):
        """Check if this message is a reply to another message."""
        return self.parent_message is not None

    def get_thread_root(self):
        """Get the root message of the conversation thread."""
        message = self
        while message.parent_message:
            message = message.parent_message
        return message

    def get_all_replies(self):
        """
        Recursively get all replies to this message using optimized ORM queries.
        Returns a queryset of all descendant messages.
        """
        return Message.objects.filter(parent_message=self).select_related(
            'sender', 'receiver', 'parent_message'
        ).prefetch_related('replies')

    def get_reply_count(self):
        """Get the total count of direct replies to this message."""
        return self.replies.count()

    def get_total_reply_count(self):
        """
        Get the total count of all replies (including nested) recursively.
        """
        count = self.replies.count()
        for reply in self.replies.all():
            count += reply.get_total_reply_count()
        return count

    def get_thread_messages(self):
        """
        Get all messages in the same thread (root and all descendants).
        Uses optimized queries with prefetch_related.
        """
        root = self.get_thread_root()
        return Message.objects.filter(
            models.Q(message_id=root.message_id) |
            models.Q(parent_message=root) |
            models.Q(parent_message__parent_message=root) |
            models.Q(parent_message__parent_message__parent_message=root)
        ).select_related(
            'sender', 'receiver', 'parent_message'
        ).prefetch_related('replies').order_by('timestamp')

    def get_conversation_participants(self):
        """Get all unique participants in this conversation thread."""
        root = self.get_thread_root()
        thread_messages = root.get_thread_messages()
        
        participants = set()
        for msg in thread_messages:
            participants.add(msg.sender)
            participants.add(msg.receiver)
        
        return list(participants)

    @staticmethod
    def get_root_messages_optimized():
        """
        Get all root messages (messages with no parent) with optimized queries.
        Uses select_related and prefetch_related to minimize database hits.
        """
        return Message.objects.filter(
            parent_message__isnull=True
        ).select_related(
            'sender', 'receiver'
        ).prefetch_related(
            'replies__sender',
            'replies__receiver',
            'replies__replies'
        ).order_by('-timestamp')

    @staticmethod
    def get_conversation_tree(root_message):
        """
        Build a complete conversation tree with all nested replies.
        Returns a dictionary structure representing the threaded conversation.
        """
        def build_tree(message):
            replies = message.replies.select_related(
                'sender', 'receiver'
            ).prefetch_related('replies').order_by('timestamp')
            
            return {
                'message': message,
                'replies': [build_tree(reply) for reply in replies]
            }
        
        return build_tree(root_message)


class MessageHistory(models.Model):
    """
    MessageHistory model for storing previous versions of edited messages.
    """
    history_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='history'
    )
    old_content = models.TextField()
    edited_at = models.DateTimeField(auto_now_add=True)
    edited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='message_edits'
    )

    class Meta:
        ordering = ['-edited_at']
        verbose_name = 'Message History'
        verbose_name_plural = 'Message Histories'
        indexes = [
            models.Index(fields=['message', '-edited_at']),
        ]

    def __str__(self):
        return f"History for message {self.message.message_id} edited at {self.edited_at}"


class Notification(models.Model):
    """
    Notification model for storing user notifications.
    Automatically created when a new message is received.
    """
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('reply', 'New Reply'),
        ('system', 'System Notification'),
    )

    notification_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='message'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.content[:50]}"

    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.save()
