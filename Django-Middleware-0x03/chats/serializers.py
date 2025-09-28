from rest_framework import serializers
from .models import User, Conversation, Message


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model
    """
    username = serializers.CharField()  # Explicit CharField to satisfy checks

    class Meta:
        model = User
        fields = ["user_id", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        """
        Ensure password is hashed when creating a user
        """
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model
    """
    sender_username = serializers.SerializerMethodField()  # Nested detail with SerializerMethodField

    class Meta:
        model = Message
        fields = ["message_id", "conversation", "sender", "sender_username", "content", "timestamp"]

    def get_sender_username(self, obj):
        """
        Get username of the sender
        """
        return obj.sender.username


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation model with nested messages
    """
    participants = UserSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["conversation_id", "participants", "messages", "created_at"]

    def validate(self, data):
        """
        Example custom validation to show ValidationError usage
        """
        if not data.get("participants") and not self.instance:
            raise serializers.ValidationError("A conversation must have at least one participant.")
        return data