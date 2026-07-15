from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Board, List, Card, Comment

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'card', 'author', 'text', 'created_at']
        read_only_fields = ['author']


class CardSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        source='assignee', queryset=User.objects.all(),
        write_only=True, required=False, allow_null=True,
    )
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Card
        fields = [
            'id', 'list', 'title', 'description', 'position',
            'assignee', 'assignee_id', 'due_date', 'comments',
            'created_at', 'updated_at',
        ]


class CardMoveSerializer(serializers.Serializer):
    list_id = serializers.PrimaryKeyRelatedField(
        source='list', queryset=List.objects.all()
    )
    position = serializers.FloatField()


class ListSerializer(serializers.ModelSerializer):
    cards = CardSerializer(many=True, read_only=True)

    class Meta:
        model = List
        fields = ['id', 'board', 'title', 'position', 'cards', 'created_at']


class ListReorderSerializer(serializers.Serializer):
    position = serializers.FloatField()


class ListLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = List
        fields = ['id', 'board', 'title', 'position']


class BoardSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    lists = ListSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = [
            'id', 'title', 'owner', 'members', 'lists',
            'created_at', 'updated_at',
        ]


class BoardWriteSerializer(serializers.ModelSerializer):
    member_ids = serializers.PrimaryKeyRelatedField(
        source='members', queryset=User.objects.all(),
        many=True, write_only=True, required=False,
    )

    class Meta:
        model = Board
        fields = ['id', 'title', 'member_ids']

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        board = Board.objects.create(
            owner=self.context['request'].user, **validated_data
        )
        if members:
            board.members.set(members)
        return board
