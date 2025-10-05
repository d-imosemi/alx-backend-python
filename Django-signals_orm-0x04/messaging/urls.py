from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Message detail view with history
    path('message/<uuid:message_id>/', views.message_detail, name='message_detail'),
    
    # API endpoint for message history as JSON
    path('api/message/<uuid:message_id>/history/', views.message_history_json, name='message_history_json'),
    
    # User's messages view
    path('my-messages/', views.user_messages, name='user_messages'),
    
    # Inbox and unread messages views
    path('inbox/', views.inbox, name='inbox'),
    path('unread/', views.unread_messages, name='unread_messages'),
    path('unread/<str:sender_username>/', views.unread_by_sender, name='unread_by_sender'),
    path('mark-read/<uuid:message_id>/', views.mark_message_read, name='mark_message_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    
    # Message preview with optimization
    path('preview/', views.message_preview_optimized, name='message_preview'),
    
    # API endpoint for unread count
    path('api/unread-count/', views.unread_count_api, name='unread_count_api'),
    
    # Threaded conversation views
    path('conversation/<uuid:message_id>/', views.conversation_thread, name='conversation_thread'),
    path('conversations/', views.all_conversations, name='all_conversations'),
    path('reply/<uuid:parent_message_id>/', views.create_reply, name='create_reply'),
    
    # API endpoint for conversation tree as JSON
    path('api/conversation/<uuid:message_id>/tree/', views.conversation_tree_json, name='conversation_tree_json'),
    
    # User account deletion views
    path('account/delete/', views.delete_user_account, name='delete_user_account'),
    path('account/delete/confirm/', views.delete_user, name='delete_user'),
    path('account/deleted/', views.account_deleted, name='account_deleted'),
    
    # API endpoint for user data summary
    path('api/user/data-summary/', views.user_data_summary, name='user_data_summary'),
]
