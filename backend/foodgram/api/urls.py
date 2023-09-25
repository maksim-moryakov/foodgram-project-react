from api.views import (AuthTokenLogoutView, AuthTokenView, IngredientViewSet,
                       RecipeViewSet, TagViewSet, UserViewSet)
from django.urls import include, path
from rest_framework import routers

router = routers.SimpleRouter()
router.register('users', UserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('auth/token/login/', AuthTokenView.as_view()),
    path('auth/token/logout/', AuthTokenLogoutView.as_view()),
    path('', include(router.urls)),
]
