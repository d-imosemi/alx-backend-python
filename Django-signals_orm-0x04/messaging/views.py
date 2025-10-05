from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_page
from django.db.models import Q, Prefetch, Count
from .models import Message, MessageHistory


@login_required
def message_detail(request, message_id):
    """
    View to display a message with its edit history and threaded replies.
    Uses optimized ORM queries with prefetch_related and select_related.
    
    Args:
        request: HTTP request object
        message_id: UUID of the message to display
    
    Returns:
        Rendered template with message, history, and threaded replies
    """
    # Optimized query using select_related for foreign keys
    message = get_object_or_404(
        Message.objects.select_related('sender', 'receiver', 'parent_message'),
        message_id=message_id
    )
    
    # Get all history entries for this message
    history_entries = MessageHistory.objects.filter(
        message=message
    ).select_related('edited_by').order_by('-edited_at')
    
    # Get conversation tree using optimized recursive query
    conversation_tree = Message.get_conversation_tree(message.get_thread_root())
    
    # Get all participants in the thread
    participants = message.get_conversation_participants()
    
    context = {
        'message': message,
        'history_entries': history_entries,
        'has_history': history_entries.exists(),
        'conversation_tree': conversation_tree,
        'participants': participants,
        'is_reply': message.is_reply(),
        'reply_count': message.get_reply_count(),
        'total_reply_count': message.get_total_reply_count(),
    }
    
    return render(request, 'messaging/message_detail.html', context)


@login_required
def message_history_json(request, message_id):
    """
    API endpoint to get message history as JSON.
    
    Args:
        request: HTTP request object
        message_id: UUID of the message
    
    Returns:
        JSON response with message history
    """
    message = get_object_or_404(Message, message_id=message_id)
    
    # Get all history entries
    history_entries = MessageHistory.objects.filter(message=message).order_by('-edited_at')
    
    # Build response data
    history_data = []
    for entry in history_entries:
        history_data.append({
            'history_id': str(entry.history_id),
            'old_content': entry.old_content,
            'edited_at': entry.edited_at.isoformat(),
            'edited_by': entry.edited_by.username if entry.edited_by else None
        })
    
    response_data = {
        'message_id': str(message.message_id),
        'current_content': message.content,
        'edited': message.edited,
        'last_edited_at': message.last_edited_at.isoformat() if message.last_edited_at else None,
        'history': history_data
    }
    
    return JsonResponse(response_data)


@login_required
def user_messages(request):
    """
    View to display all messages for the logged-in user.
    Shows both sent and received messages with edit indicators.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with user's messages
    """
    user = request.user
    
    # Get sent and received messages
    sent_messages = Message.objects.filter(sender=user).order_by('-timestamp')
    received_messages = Message.objects.filter(receiver=user).order_by('-timestamp')
    
    context = {
        'sent_messages': sent_messages,
        'received_messages': received_messages,
    }
    
    return render(request, 'messaging/user_messages.html', context)


@login_required
def delete_user_account(request):
    """
    View to display user account deletion confirmation page.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with deletion confirmation
    """
    if request.method == 'GET':
        # Display confirmation page with user statistics
        user = request.user
        
        # Get counts of user-related data
        sent_messages_count = Message.objects.filter(sender=user).count()
        received_messages_count = Message.objects.filter(receiver=user).count()
        notifications_count = user.notifications.count()
        
        context = {
            'sent_messages_count': sent_messages_count,
            'received_messages_count': received_messages_count,
            'notifications_count': notifications_count,
            'total_messages': sent_messages_count + received_messages_count,
        }
        
        return render(request, 'messaging/delete_account.html', context)


@login_required
@require_POST
def delete_user(request):
    """
    View to handle user account deletion.
    Deletes the user account and all related data via signals.
    
    Args:
        request: HTTP request object with POST data
    
    Returns:
        Redirect to homepage after deletion
    """
    user = request.user
    username = user.username
    
    # Verify confirmation (optional security check)
    confirmation = request.POST.get('confirmation', '')
    
    if confirmation.lower() == 'delete':
        try:
            # Log out the user first
            logout(request)
            
            # Delete the user (this triggers post_delete signal)
            # The signal will automatically clean up all related data
            user.delete()
            
            # Add success message
            messages.success(
                request,
                f'Account "{username}" has been successfully deleted along with all associated data.'
            )
            
            return redirect('account_deleted')
        
        except Exception as e:
            messages.error(
                request,
                f'An error occurred while deleting your account: {str(e)}'
            )
            return redirect('delete_user_account')
    else:
        messages.error(
            request,
            'Account deletion failed. Please type "delete" to confirm.'
        )
        return redirect('delete_user_account')


def account_deleted(request):
    """
    View to display account deletion success page.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template confirming account deletion
    """
    return render(request, 'messaging/account_deleted.html')


@login_required
def user_data_summary(request):
    """
    API endpoint to get summary of user's data (for display before deletion).
    
    Args:
        request: HTTP request object
    
    Returns:
        JSON response with user data summary
    """
    user = request.user
    
    # Get detailed counts
    sent_messages = Message.objects.filter(sender=user)
    received_messages = Message.objects.filter(receiver=user)
    notifications = user.notifications.all()
    message_edits = MessageHistory.objects.filter(edited_by=user)
    
    data = {
        'username': user.username,
        'email': user.email,
        'sent_messages_count': sent_messages.count(),
        'received_messages_count': received_messages.count(),
        'total_messages': sent_messages.count() + received_messages.count(),
        'notifications_count': notifications.count(),
        'unread_notifications_count': notifications.filter(is_read=False).count(),
        'message_edits_count': message_edits.count(),
        'account_created': user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
    }
    
    return JsonResponse(data)


@login_required
@cache_page(60)  # cache for 60 seconds
def conversation_thread(request, message_id):
    """
    View to display a complete conversation thread.
    Uses advanced ORM techniques for efficient querying.
    
    Args:
        request: HTTP request object
        message_id: UUID of any message in the thread
    
    Returns:
        Rendered template with threaded conversation
    """
    # Get the message with optimized query
    message = get_object_or_404(
        Message.objects.select_related('sender', 'receiver', 'parent_message'),
        message_id=message_id
    )
    
    # Get root message of the thread
    root_message = message.get_thread_root()
    
    # Build conversation tree using optimized recursive query
    conversation_tree = Message.get_conversation_tree(root_message)
    
    # Get all participants
    participants = message.get_conversation_participants()
    
    # Get message count in thread
    thread_messages = root_message.get_thread_messages()
    message_count = thread_messages.count()
    
    context = {
        'root_message': root_message,
        'conversation_tree': conversation_tree,
        'participants': participants,
        'message_count': message_count,
        'current_message': message,
    }
    
    return render(request, 'messaging/conversation_thread.html', context)


@login_required
def create_reply(request, parent_message_id):
    """
    View to create a reply to an existing message.
    
    Args:
        request: HTTP request object
        parent_message_id: UUID of the parent message
    
    Returns:
        Redirect to conversation thread
    """
    if request.method == 'POST':
        parent_message = get_object_or_404(Message, message_id=parent_message_id)
        content = request.POST.get('content', '').strip()
        
        if content:
            # Create reply
            reply = Message.objects.create(
                sender=request.user,
                receiver=parent_message.sender,  # Reply to original sender
                content=content,
                parent_message=parent_message
            )
            
            messages.success(request, 'Reply posted successfully!')
            return redirect('messaging:conversation_thread', message_id=reply.message_id)
        else:
            messages.error(request, 'Reply content cannot be empty.')
    
    return redirect('messaging:message_detail', message_id=parent_message_id)


@login_required
@cache_page(60)  # cache for 60 seconds
def all_conversations(request):
    """
    View to display all root conversations with optimized queries.
    Uses prefetch_related to minimize database hits.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with all conversations
    """
    user = request.user
    
    # Get all root messages where user is sender or receiver
    # Using optimized queries with select_related and prefetch_related
    root_messages = Message.objects.filter(
        Q(sender=user) | Q(receiver=user),
        parent_message__isnull=True
    ).select_related(
        'sender', 'receiver'
    ).prefetch_related(
        Prefetch('replies',
                 queryset=Message.objects.select_related('sender', 'receiver'))
    ).annotate(
        reply_count=Count('replies')
    ).order_by('-timestamp')
    
    context = {
        'root_messages': root_messages,
    }
    
    return render(request, 'messaging/all_conversations.html', context)


@login_required
def conversation_tree_json(request, message_id):
    """
    API endpoint to get conversation tree as JSON.
    Uses recursive querying for nested replies.
    
    Args:
        request: HTTP request object
        message_id: UUID of any message in the thread
    
    Returns:
        JSON response with conversation tree
    """
    message = get_object_or_404(Message, message_id=message_id)
    root_message = message.get_thread_root()
    
    def serialize_tree(tree_node):
        """Recursively serialize conversation tree."""
        msg = tree_node['message']
        return {
            'message_id': str(msg.message_id),
            'sender': msg.sender.username,
            'receiver': msg.receiver.username,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'edited': msg.edited,
            'is_reply': msg.is_reply(),
            'replies': [serialize_tree(reply) for reply in tree_node['replies']]
        }
    
    conversation_tree = Message.get_conversation_tree(root_message)
    serialized_tree = serialize_tree(conversation_tree)
    
    return JsonResponse(serialized_tree)


@login_required
def unread_messages(request):
    """
    View to display only unread messages for the logged-in user.
    Uses custom UnreadMessagesManager and .only() for optimization.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with unread messages
    """
    user = request.user
    
    # Use custom manager to get unread messages
    # Optimize with .only() to retrieve only necessary fields
    unread_msgs = Message.unread.unread_for_user(user).only(
        'message_id',
        'sender__username',
        'content',
        'timestamp',
        'read',
        'parent_message'
    )
    
    # Get unread count
    unread_count = Message.unread.unread_count_for_user(user)
    
    context = {
        'unread_messages': unread_msgs,
        'unread_count': unread_count,
    }
    
    return render(request, 'messaging/unread_messages.html', context)


@login_required
def mark_message_read(request, message_id):
    """
    View to mark a specific message as read.
    
    Args:
        request: HTTP request object
        message_id: UUID of the message
    
    Returns:
        Redirect or JSON response
    """
    message = get_object_or_404(Message, message_id=message_id, receiver=request.user)
    message.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message_id': str(message_id)})
    
    messages.success(request, 'Message marked as read.')
    return redirect('messaging:unread_messages')


@login_required
def mark_all_read(request):
    """
    View to mark all messages as read for the current user.
    Uses the custom manager's mark_all_read_for_user method.
    
    Args:
        request: HTTP request object
    
    Returns:
        Redirect with success message
    """
    count = Message.unread.mark_all_read_for_user(request.user)
    
    messages.success(request, f'{count} message(s) marked as read.')
    return redirect('messaging:user_messages')


@login_required
def unread_by_sender(request, sender_username):
    """
    View to display unread messages from a specific sender.
    Uses custom manager and .only() optimization.
    
    Args:
        request: HTTP request object
        sender_username: Username of the sender
    
    Returns:
        Rendered template with unread messages from sender
    """
    sender = get_object_or_404(User, username=sender_username)
    
    # Use custom manager with .only() optimization
    unread_msgs = Message.unread.unread_by_sender(
        request.user, sender
    ).only(
        'message_id',
        'sender__username',
        'content',
        'timestamp',
        'read'
    )
    
    context = {
        'unread_messages': unread_msgs,
        'sender': sender,
        'unread_count': unread_msgs.count(),
    }
    
    return render(request, 'messaging/unread_by_sender.html', context)


@login_required
def inbox(request):
    """
    View to display user's inbox with unread message count.
    Uses optimized queries with .only() to minimize data transfer.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with inbox
    """
    user = request.user
    
    # Get all received messages with optimization
    received_messages = Message.objects.filter(
        receiver=user
    ).select_related('sender').only(
        'message_id',
        'sender__username',
        'content',
        'timestamp',
        'read',
        'edited'
    ).order_by('-timestamp')[:50]  # Limit to last 50 messages
    
    # Get unread count using custom manager
    unread_count = Message.unread.unread_count_for_user(user)
    
    # Get unread threads count
    unread_threads = Message.unread.unread_threads_for_user(user).count()
    
    context = {
        'received_messages': received_messages,
        'unread_count': unread_count,
        'unread_threads': unread_threads,
    }
    
    return render(request, 'messaging/inbox.html', context)


@login_required
def unread_count_api(request):
    """
    API endpoint to get unread message count.
    Useful for real-time updates via AJAX.
    
    Args:
        request: HTTP request object
    
    Returns:
        JSON response with unread count
    """
    user = request.user
    unread_count = Message.unread.unread_count_for_user(user)
    unread_threads = Message.unread.unread_threads_for_user(user).count()
    
    return JsonResponse({
        'unread_count': unread_count,
        'unread_threads': unread_threads,
    })


@login_required
def message_preview_optimized(request):
    """
    View to display message previews with minimal data.
    Uses .only() to fetch only essential fields.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with message previews
    """
    user = request.user
    
    # Get messages with only preview fields
    messages_preview = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).only(
        'message_id',
        'sender__username',
        'receiver__username',
        'content',
        'timestamp',
        'read'
    ).select_related('sender', 'receiver').order_by('-timestamp')[:20]
    
    context = {
        'messages_preview': messages_preview,
    }
    
    return render(request, 'messaging/message_preview.html', context)
