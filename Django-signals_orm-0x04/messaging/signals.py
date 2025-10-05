from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Message, Notification, MessageHistory


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Signal handler that creates a notification when a new message is created.
    Differentiates between new messages and replies.
    
    Args:
        sender: The model class (Message)
        instance: The actual Message instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Determine notification type based on whether it's a reply
        if instance.parent_message:
            notification_type = 'reply'
            notification_content = f"You have a new reply from {instance.sender.username}"
            
            # Notify the original sender as well if different from receiver
            original_sender = instance.parent_message.sender
            if original_sender != instance.receiver and original_sender != instance.sender:
                Notification.objects.create(
                    user=original_sender,
                    message=instance,
                    notification_type='reply',
                    content=f"{instance.sender.username} replied to your message"
                )
        else:
            notification_type = 'message'
            notification_content = f"You have a new message from {instance.sender.username}"
        
        # Create notification for the receiver
        Notification.objects.create(
            user=instance.receiver,
            message=instance,
            notification_type=notification_type,
            content=notification_content
        )
        
        print(f"Notification created for {instance.receiver.username} about {notification_type} from {instance.sender.username}")


@receiver(post_save, sender=Message)
def log_message_creation(sender, instance, created, **kwargs):
    """
    Additional signal handler to log message creation.
    This demonstrates that multiple signals can listen to the same event.
    
    Args:
        sender: The model class (Message)
        instance: The actual Message instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        print(f"New message logged: {instance.message_id} from {instance.sender.username} to {instance.receiver.username}")


@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    """
    Signal handler that logs message edits before they are saved.
    Captures the old content and stores it in MessageHistory.
    
    Args:
        sender: The model class (Message)
        instance: The actual Message instance being saved
        **kwargs: Additional keyword arguments
    """
    # Only process if this is an existing message (not a new one)
    if instance.pk:
        try:
            # Get the old version of the message from the database
            old_message = Message.objects.get(pk=instance.pk)
            
            # Check if the content has changed
            if old_message.content != instance.content:
                # Create a history entry with the old content
                MessageHistory.objects.create(
                    message=instance,
                    old_content=old_message.content,
                    edited_by=instance.sender
                )
                
                # Mark the message as edited
                instance.edited = True
                instance.last_edited_at = timezone.now()
                
                print(f"Message {instance.message_id} edited. Old content saved to history.")
        
        except Message.DoesNotExist:
            # This shouldn't happen, but handle it gracefully
            pass


@receiver(post_delete, sender=User)
def delete_user_related_data(sender, instance, **kwargs):
    """
    Signal handler that cleans up all user-related data when a user is deleted.
    
    This handles:
    - Messages sent by the user
    - Messages received by the user
    - Notifications for the user
    - Message history entries edited by the user
    
    Args:
        sender: The model class (User)
        instance: The actual User instance being deleted
        **kwargs: Additional keyword arguments
    """
    username = instance.username
    
    # Delete all messages sent by the user
    sent_messages_count = Message.objects.filter(sender=instance).count()
    Message.objects.filter(sender=instance).delete()
    print(f"Deleted {sent_messages_count} messages sent by {username}")
    
    # Delete all messages received by the user
    received_messages_count = Message.objects.filter(receiver=instance).count()
    Message.objects.filter(receiver=instance).delete()
    print(f"Deleted {received_messages_count} messages received by {username}")
    
    # Delete all notifications for the user
    notifications_count = Notification.objects.filter(user=instance).count()
    Notification.objects.filter(user=instance).delete()
    print(f"Deleted {notifications_count} notifications for {username}")
    
    # Delete message history entries edited by the user
    # Note: History entries linked to deleted messages are automatically deleted via CASCADE
    history_count = MessageHistory.objects.filter(edited_by=instance).count()
    MessageHistory.objects.filter(edited_by=instance).update(edited_by=None)
    print(f"Cleared edited_by reference for {history_count} history entries by {username}")
    
    print(f"Successfully cleaned up all data for user: {username}")
