from django.db import models


class UnreadMessagesManager(models.Manager):
    """
    Custom manager for filtering unread messages.
    """
    
    def unread_for_user(self, user):
        """
        Get all unread messages for a specific user.
        
        Args:
            user: User object to filter messages for
            
        Returns:
            QuerySet of unread messages optimized with select_related
        """
        return self.get_queryset().filter(
            receiver=user,
            read=False
        ).select_related('sender', 'receiver').order_by('-timestamp')
    
    def unread_count_for_user(self, user):
        """
        Get count of unread messages for a user.
        
        Args:
            user: User object
            
        Returns:
            Integer count of unread messages
        """
        return self.get_queryset().filter(
            receiver=user,
            read=False
        ).count()
    
    def unread_by_sender(self, user, sender):
        """
        Get unread messages from a specific sender.
        
        Args:
            user: Receiver user object
            sender: Sender user object
            
        Returns:
            QuerySet of unread messages from sender
        """
        return self.get_queryset().filter(
            receiver=user,
            sender=sender,
            read=False
        ).select_related('sender', 'receiver').order_by('-timestamp')
    
    def mark_all_read_for_user(self, user):
        """
        Mark all messages as read for a user.
        
        Args:
            user: User object
            
        Returns:
            Number of messages marked as read
        """
        return self.get_queryset().filter(
            receiver=user,
            read=False
        ).update(read=True)
    
    def unread_threads_for_user(self, user):
        """
        Get unread messages that are root messages (start of threads).
        
        Args:
            user: User object
            
        Returns:
            QuerySet of unread root messages
        """
        return self.get_queryset().filter(
            receiver=user,
            read=False,
            parent_message__isnull=True
        ).select_related('sender', 'receiver').order_by('-timestamp')
