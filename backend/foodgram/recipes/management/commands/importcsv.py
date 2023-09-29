import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    ''' Загрузка данных из JSON-файла '''

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Загружаем ингридиенты!'))
        with open('data/ingredients.json', encoding='utf-8',
                  ) as data_file_ingredients:
            ingredient_data = json.loads(data_file_ingredients.read())
            for ingredients in ingredient_data:
                Ingredient.objects.get_or_create(**ingredients)

        self.stdout.write(self.style.SUCCESS('Ингридиенты загружены!'))
