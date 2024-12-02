import json
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Преобразует данные в формат фикстур Django'

    def add_arguments(self, parser):
        parser.add_argument(
            'input_file',
            type=str,
            help='Путь к исходному JSON файлу',
        )
        parser.add_argument(
            '--output_file',
            type=str,
            default='ingredients.json',
            help='Путь для выходного файла (по умолчанию: ingredients.json)',
        )
        parser.add_argument(
            '--model',
            type=str,
            default='recipe.Ingredient',
            help='Моедль для фикстуры (по умолчанию: recipe.Ingredient)',
        )

    def handle(self, *args, **kwargs):
        input_file = Path(kwargs['input_file'])
        output_file = Path(kwargs['output_file'])
        model_name = kwargs['model']

        if not input_file.exists():
            self.stderr.write(
                self.style.ERROR(
                    f'Файл {input_file} не найден. Проверьте путь.'
                )
            )
            return

        try:
            raw_data = json.loads(input_file.read_text(encoding='utf-8'))
            self.stdout.write(
                f'Успешно прочитано {len(raw_data)} записей из {input_file}'
            )

            formatted_data = [
                {
                    'model': model_name,
                    'pk': pk,
                    'fields': {
                        'name': item['name'],
                        'measurement_unit': item['measurement_unit']
                    }
                }
                for pk, item in enumerate(raw_data, start=1)
            ]

            output_file.write_text(
                json.dumps(formatted_data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            self.stdout.write(self.style.SUCCESS(
                f'Фикстура успешно сохранена в {output_file}'
            )
            )

        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f'Ошибка загрузки JSON: {e}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ошибка: {e}'))
