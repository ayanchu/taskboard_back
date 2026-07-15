from rest_framework.routers import DefaultRouter

from .views import BoardViewSet, ListViewSet, CardViewSet, CommentViewSet

router = DefaultRouter()
router.register('boards', BoardViewSet, basename='board')
router.register('lists', ListViewSet, basename='list')
router.register('cards', CardViewSet, basename='card')
router.register('comments', CommentViewSet, basename='comment')

urlpatterns = router.urls
