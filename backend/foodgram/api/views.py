from csv import writer

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import TokenCreateView, TokenDestroyView
from recipes.models import (Favorite, Ingredient, Recipe, ShoppingCart,
                            Subscription, Tag, User)
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from api.permissions import (AuthenticatedOrReadOnlyPermission,
                             IsOwnerOrReadOnlyPermission)
from api.serializers import (FavoriteShoppingCartSerializer,
                             IngredientGetSerializer, PasswordSerializer,
                             RecipeGetSerializer, RecipeWriteSerializer,
                             SubscribeSerializer, TagSerializer,
                             UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для доступа к пользователям."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrReadOnlyPermission]
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
                {'Такой email существует.'},
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
                    "Попытка повторного добавления",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                Subscription.objects.create(user=user, author=author)
            except IntegrityError as err:
                if 'unique constraint' in err.args:
                    return Response(
                        "Попытка повторного добавления",
                        status=status.HTTP_400_BAD_REQUEST,
                    )

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
                "Попытка не существующего удаления",
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
        recipes_limit = request.query_params.get('recipes_limit')

        queryset = (
            User.objects.filter(
                id__in=Subscription
                .objects.filter(user=user)
                .values_list('author', flat=True)
            )
        )

        if recipes_limit is not None:
            queryset = queryset[:int(recipes_limit)]

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscribeSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

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
    permission_classes = [AuthenticatedOrReadOnlyPermission]
    lookup_field = 'id'

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от метода"""
        if (
            self.action == 'create'
            or self.action == 'update'
            or self.action == 'partial_update'
        ):
            return RecipeWriteSerializer
        return RecipeGetSerializer

    def list(self, request, *args, **kwargs):
        """Возвращает список рецептов с фильтрацией по параметрам"""
        tags = request.query_params.getlist('tags')
        author = request.query_params.get('author')
        if request.user.is_authenticated:
            user = User.objects.get(username=request.user)
        else:
            user = None
        favor = request.query_params.get('is_favorited')
        shop_cart = request.query_params.get('is_in_shopping_cart')

        if user and favor == '1':
            queryset = (
                Recipe.objects
                .filter(id__in=Favorite.objects
                        .filter(user=user).values('recipe__id'))
                .filter(tags__slug__in=tags)
            )
        elif user and shop_cart == '1':
            queryset = (
                Recipe.objects
                .filter(id__in=ShoppingCart.objects
                        .filter(user=user).values('recipe__id'))
            )
        else:
            if author:
                queryset = self.filter_queryset(self.get_queryset()).filter(
                    tags__slug__in=tags, author=User.objects.get(id=author),
                )
            else:
                queryset = self.filter_queryset(self.get_queryset()).filter(
                    tags__slug__in=tags,
                )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
                    "Попытка повторного добавления",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                ShoppingCart.objects.create(user=user, recipe=recipe)
            except IntegrityError as err:
                if 'unique constraint' in err.args:
                    return Response(
                        "Попытка повторного добавления",
                        status=status.HTTP_400_BAD_REQUEST,
                    )

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
                "Попытка не существующего удаления",
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
                    "Попытка повторного добавления",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                Favorite.objects.create(user=user, recipe=recipe)
            except IntegrityError as err:
                if 'unique constraint' in err.args:
                    return Response(
                        "Попытка повторного добавления",
                        status=status.HTTP_400_BAD_REQUEST,
                    )

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
                "Попытка не существующего удаления",
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
