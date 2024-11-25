import json
import os

input_file = 'ingredients_raw.json'
output_file = 'ingredients.json'

if not os.path.exists(input_file):
    print(f'Файл {input_file} не найден. Проверьте путь.')
    exit()

model_name = 'recipe.Ingredient'

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    print(f'Успешно прочитано {len(raw_data)} записей из {input_file}')

    formatted_data = []
    for pk, item in enumerate(raw_data, start=1):
        formatted_data.append({
            'model': model_name,
            'pk': pk,
            'fields': {
                'name': item['name'],
                'measurement_unit': item['measurement_unit']
            }
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)

    print(f'Фикстура успешно сохранена в {output_file}')

except Exception as e:
    print(f'Ошибка: {e}')
