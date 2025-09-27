from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView


from .auth import CustomTokenObtainPairSerializer
from .permissions import IsParticipantOfConversation, IsMessageOwner
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, UserSerializer
from .pagination import LargeResultsSetPagination, StandardResultsSetPagination
from .filters import MessageFilter


User = get_user_model()

class UserViewset(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()
    

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsParticipantOfConversation]
    pagination_class = LargeResultsSetPagination
    filter_backends = [MessageFilter]
    filterset_fields = ['participants']

    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_pk')  # note the lookup key
        # will break since there is no field for conversation in message
        return Message.objects.filter(
            conversation_id=conversation_id,
            conversation__participants=self.request.user
        ).order_by('sent_at')

    def perform_create(self, serializer):
        # Add current user to participants automatically (if not already added by serializer)
        conversation = serializer.save()
        conversation.participants.add(self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsMessageOwner]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user)

    def create(self, request, *args, **kwargs):
        conversation_id = self.kwargs.get('conversation_pk')
        conversation = get_object_or_404(Conversation, conversation_id=conversation_id)

        # Check if user is a participant
        if request.user not in conversation.participants.all():
            return Response(
                {"detail": "You are not a participant in this conversation."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data, context={
            'request': request,
            'conversation': conversation
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)



class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
