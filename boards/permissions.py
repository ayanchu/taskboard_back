from rest_framework import permissions


class IsBoardMember(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        board = self._resolve_board(obj)
        if board is None:
            return False
        return board.is_member(request.user)

    def _resolve_board(self, obj):
        if hasattr(obj, 'is_member'):
            return obj
        if hasattr(obj, 'board'):
            return obj.board
        if hasattr(obj, 'list'):
            return obj.list.board
        if hasattr(obj, 'card'):
            return obj.card.list.board
        return None
