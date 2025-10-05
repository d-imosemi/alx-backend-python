from django.contrib import admin
from .models import Message, Notification, MessageHistory


class MessageHistoryInline(admin.TabularInline):
    """
    Inline admin for displaying message edit history.
    """
    model = MessageHistory
    extra = 0
    readonly_fields = ['history_id', 'old_content', 'edited_at', 'edited_by']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        """Prevent manual addition of history entries."""
        return False


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin interface for Message model with threading and read status support.
    """
    list_display = ['message_id', 'sender', 'receiver', 'content_preview', 'timestamp', 'read', 'edited', 'is_reply_display', 'reply_count_display']
    list_filter = ['timestamp', 'read', 'edited', 'sender', 'receiver', 'parent_message']
    search_fields = ['sender__username', 'receiver__username', 'content']
    readonly_fields = ['message_id', 'timestamp', 'edited', 'last_edited_at']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    inlines = [MessageHistoryInline]
    actions = ['mark_as_read', 'mark_as_unread']
    
    fieldsets = (
        ('Message Information', {
            'fields': ('message_id', 'sender', 'receiver', 'content')
        }),
        ('Status', {
            'fields': ('read',)
        }),
        ('Threading', {
            'fields': ('parent_message',),
            'description': 'Set parent message to create a reply'
        }),
        ('Timestamp & Edit Info', {
            'fields': ('timestamp', 'edited', 'last_edited_at')
        }),
    )

    def content_preview(self, obj):
        """Display first 50 characters of content."""
        preview = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        badges = []
        if obj.edited:
            badges.append('edited')
        if not obj.read:
            badges.append('unread')
        if badges:
            return f"{preview} ({', '.join(badges)})"
        return preview
    
    content_preview.short_description = 'Content Preview'

    def is_reply_display(self, obj):
        """Display if message is a reply."""
        return '✓' if obj.is_reply() else '✗'
    
    is_reply_display.short_description = 'Is Reply'
    is_reply_display.boolean = True

    def reply_count_display(self, obj):
        """Display number of direct replies."""
        count = obj.get_reply_count()
        return f"{count} replies" if count != 1 else f"{count} reply"
    
    reply_count_display.short_description = 'Replies'

    def mark_as_read(self, request, queryset):
        """Mark selected messages as read."""
        updated = queryset.update(read=True)
        self.message_user(request, f'{updated} message(s) marked as read.')
    
    mark_as_read.short_description = 'Mark selected messages as read'

    def mark_as_unread(self, request, queryset):
        """Mark selected messages as unread."""
        updated = queryset.update(read=False)
        self.message_user(request, f'{updated} message(s) marked as unread.')
    
    mark_as_unread.short_description = 'Mark selected messages as unread'


@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for MessageHistory model.
    """
    list_display = ['history_id', 'message', 'old_content_preview', 'edited_at', 'edited_by']
    list_filter = ['edited_at', 'edited_by']
    search_fields = ['message__message_id', 'old_content', 'edited_by__username']
    readonly_fields = ['history_id', 'message', 'old_content', 'edited_at', 'edited_by']
    date_hierarchy = 'edited_at'
    ordering = ['-edited_at']
    
    fieldsets = (
        ('History Information', {
            'fields': ('history_id', 'message', 'old_content')
        }),
        ('Edit Details', {
            'fields': ('edited_at', 'edited_by')
        }),
    )

    def old_content_preview(self, obj):
        """Display first 50 characters of old content."""
        return obj.old_content[:50] + '...' if len(obj.old_content) > 50 else obj.old_content
    
    old_content_preview.short_description = 'Old Content Preview'

    def has_add_permission(self, request):
        """Prevent manual addition of history entries."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of history entries."""
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification model.
    """
    list_display = ['notification_id', 'user', 'notification_type', 'content_preview', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at', 'user']
    search_fields = ['user__username', 'content']
    readonly_fields = ['notification_id', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('notification_id', 'user', 'notification_type', 'content')
        }),
        ('Related Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']

    def content_preview(self, obj):
        """Display first 50 characters of content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    
    content_preview.short_description = 'Content Preview'

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marked as read.')
    
    mark_as_read.short_description = 'Mark selected notifications as read'

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread."""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    
    mark_as_unread.short_description = 'Mark selected notifications as unread'
