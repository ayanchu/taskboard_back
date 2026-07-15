from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Board, List, Card, Comment
from .permissions import IsBoardMember
from .serializers import (
    RegisterSerializer,
    BoardSerializer,
    BoardWriteSerializer,
    ListSerializer,
    ListLightSerializer,
    ListReorderSerializer,
    CardSerializer,
    CardMoveSerializer,
    CommentSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class BoardViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]

    def get_queryset(self):
        user = self.request.user
        return (
            Board.objects.filter(Q(owner=user) | Q(members=user))
            .distinct()
            .prefetch_related('members', 'lists__cards__assignee', 'lists__cards__comments__author')
        )

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return BoardWriteSerializer
        return BoardSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ListViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]

    def get_queryset(self):
        user = self.request.user
        return List.objects.filter(
            Q(board__owner=user) | Q(board__members=user)
        ).distinct().select_related('board').prefetch_related('cards')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ListLightSerializer
        return ListSerializer

    def perform_create(self, serializer):
        board = serializer.validated_data['board']
        self.check_object_permissions(self.request, board)
        serializer.save()

    @action(detail=True, methods=['patch'])
    def reorder(self, request, pk=None):
        list_obj = self.get_object()
        serializer = ListReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        list_obj.position = serializer.validated_data['position']
        list_obj.save(update_fields=['position'])
        return Response(ListLightSerializer(list_obj).data)


class CardViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]

    def get_queryset(self):
        user = self.request.user
        return Card.objects.filter(
            Q(list__board__owner=user) | Q(list__board__members=user)
        ).distinct().select_related('list__board', 'assignee').prefetch_related('comments__author')

    def get_serializer_class(self):
        return CardSerializer

    def perform_create(self, serializer):
        list_obj = serializer.validated_data['list']
        self.check_object_permissions(self.request, list_obj)
        serializer.save()

    @action(detail=True, methods=['patch'])
    def move(self, request, pk=None):
        card = self.get_object()
        serializer = CardMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_list = serializer.validated_data['list']
        # Make sure the destination list belongs to a board the user can access.
        self.check_object_permissions(request, new_list)

        card.list = new_list
        card.position = serializer.validated_data['position']
        card.save(update_fields=['list', 'position'])
        return Response(CardSerializer(card).data)


class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsBoardMember]
    serializer_class = CommentSerializer

    def get_queryset(self):
        user = self.request.user
        return Comment.objects.filter(
            Q(card__list__board__owner=user) | Q(card__list__board__members=user)
        ).distinct().select_related('author', 'card')

    def perform_create(self, serializer):
        card = serializer.validated_data['card']
        self.check_object_permissions(self.request, card)
        serializer.save(author=self.request.user)
