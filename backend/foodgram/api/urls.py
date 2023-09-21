from django.urls import include, path
from rest_framework import routers
from api.views import (AuthTokenLogoutView, AuthTokenView, IngredientViewSet,
                       RecipeViewSet, TagViewSet, UserViewSet)

router = routers.SimpleRouter()
router.register('users', UserViewSet, basename='user')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('auth/token/login/', AuthTokenView.as_view()),
    path('auth/token/logout/', AuthTokenLogoutView.as_view()),
    path('', include(router.urls)),
]
