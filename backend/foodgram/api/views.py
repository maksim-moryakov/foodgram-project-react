from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import TokenCreateView, TokenDestroyView
from recipes.models import (Favorite, Ingredient, Recipe, ShoppingCart,
                            Subscription, Tag, User)
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.filters import RecipeFilter
from api.permissions import IsAuthenticatedForDetail, IsAuthenticatedOrReadOnly
from api.serializers import (FavoriteShoppingCartSerializer,
                             IngredientGetSerializer, PasswordSerializer,
                             RecipeGetSerializer, RecipeWriteSerializer,
                             SubscribeSerializer, TagSerializer,
                             UserSerializer)

from csv import writer


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для доступа к пользователям."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedForDetail]
    lookup_field = 'id'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        email = serializer.validated_data.get('email')
        if (
            self.queryset.filter(email=email).exists()
            or self.queryset.filter(username=username).exists()
        ):
            return Response(
                "Такой email уже существует.",
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request):
        user = get_object_or_404(User, username=request.user)
        serializer = self.get_serializer(
            user, data=request.data, partial=True
        )
        if serializer.is_valid():
            if not user.is_admin and 'role' in serializer.validated_data:
                serializer.validated_data.pop('role')
            serializer.save(**serializer.validated_data)
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def set_password(self, request):
        user = get_object_or_404(User, username=request.user)
        serializer = PasswordSerializer(
            user, data=request.data, partial=True
        )
        if serializer.is_valid():
            password = serializer.validated_data.pop('new_password')
            _ = serializer.validated_data.pop('current_password')
            serializer.save(password=password, **serializer.validated_data)
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, id):
        """Реализует добавление/удаление в список подписчиков"""
        user = get_object_or_404(User, username=request.user)
        author = get_object_or_404(User, id=id)
        if self.request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    "Подписка уже существует",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Subscription.objects.create(user=user, author=author)
            serializer = UserSerializer(
                author,
                context={'request': request})
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        try:
            author = Subscription.objects.get(
                user=user, author=author,
            )
        except ObjectDoesNotExist:
            return Response(
                "Подписка не существует.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        author.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscriptions(self, request):
        """Возвращает список подписки"""
        user = get_object_or_404(User, username=request.user)

        queryset = (
            User.objects.filter(
                id__in=Subscription
                .objects.filter(user=user)
                .values_list('author', flat=True)
            )
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscribeSerializer(
                page,
                many=True,
                context={'request': request}
            )
            data = serializer.data
            return self.get_paginated_response(data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AuthTokenView(TokenCreateView):
    """View класс для получения токена."""
    permission_classes = [permissions.AllowAny]


class AuthTokenLogoutView(TokenDestroyView):
    """View класс для удаления токена."""
    permission_classes = [permissions.IsAuthenticated]


class ListRetrieveViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet
):
    """Общий viewset для использования в других viewsets."""


class TagViewSet(ListRetrieveViewSet):
    """ViewSet для доступа к тегам."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class IngredientViewSet(ListRetrieveViewSet):
    """ViewSet для доступа к инградиентам."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientGetSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        """Возвращает список рецептов с фильтрацией по параметрам"""
        name = request.query_params.get('name')
        if name is not None:
            queryset = self.filter_queryset(self.get_queryset()).filter(
                name__istartswith=name,
            )
        else:
            queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов."""
    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от метода"""
        if (
            self.action == 'list'
            or self.action == 'retrieve'
        ):
            return RecipeGetSerializer
        return RecipeWriteSerializer

    def filter_queryset(self, queryset):
        """Выбор фильтра в зависимости от метода"""
        if self.action == 'list':
            return super().filter_queryset(queryset)
        return queryset

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, id):
        """Реализует добавление/удаление в список покупок"""
        user = get_object_or_404(User, username=request.user)
        recipe = get_object_or_404(Recipe, id=id)
        if self.request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    "Рецепт уже добавлен в корзину.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = FavoriteShoppingCartSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        try:
            recipe_in_cart = ShoppingCart.objects.get(
                user=user, recipe=recipe,
            )
        except ObjectDoesNotExist:
            return Response(
                "Рецепта нет в корзине.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        recipe_in_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, id):
        """Реализует добавление/удаление в избранное"""
        user = get_object_or_404(User, username=request.user)
        recipe = get_object_or_404(Recipe, id=id)
        if self.request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    "Рецепт уже добавлен в избранное.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = FavoriteShoppingCartSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        try:
            favorite = Favorite.objects.get(
                user=user, recipe=recipe,
            )
        except ObjectDoesNotExist:
            return Response(
                "Рецепта нет в избранном.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """Реализует получение списка инградиентов из рецептов"""
        user = get_object_or_404(User, username=request.user)
        result = (ShoppingCart.objects
                  .filter(user=user).select_related('recipe')
                  .values(
                      'recipe__ingredients__ingredient__name',
                      'recipe__ingredients__ingredient__measurement_unit'
                  ).annotate(
                      names=Count('recipe__ingredients__ingredient__name'),
                      amount=Sum('recipe__ingredients__amount')
                  ).order_by())
        response = HttpResponse(
            content_type='text/csv',
        )
        response['Content-Disposition'] = (
            'attachment; filename=ingredients.csv')
        csv_writer = writer(response)
        for line in result:
            csv_writer.writerow([
                line['recipe__ingredients__ingredient__name'],
                line['recipe__ingredients__ingredient__measurement_unit'],
                line['amount'],
            ])
        return response
