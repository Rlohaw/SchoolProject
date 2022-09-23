import collections
import locale
import os
import re
import time
import zipfile

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
name = input('Укажите путь к архиву: ').strip()
if not name.endswith('.zip'):
    name += '.zip'

with zipfile.ZipFile(name, mode='r') as zp:  # Открываем зип

    def clear_console():  # очистка экрана от ненужного мусора
        os.system('cls')


    def opened_file(key):
        with zp.open(*(i for i in path if key in i)) as file:
            return file


    def time_counter(f):  # Отладка по времени(декоратор)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            a = f(*args, **kwargs)
            end = time.perf_counter()
            print(end - start, 'c')
            return a

        return wrapper


    def ads():  # раздел рекламы
        def ads_cord():  # раздел частая геопозиция
            text = opened_file('geo-points').read().decode('ANSI')
            geo = re.search('<a href="(?P<site>.+)">(?P<lat>.+), (?P<lon>.+)</a>', text)
            print(f"Геопозиция на картах:{geo['site']}\n{geo['lat']}\n{geo['lon']}")

        def ads_interests():  # раздел интересы
            def user_interests():
                print(*d['Пользовательский интерес'], sep='\n')

            def other_segments():
                print(*d['Сторонний сегмент'], sep='\n')

            def all_interests():
                print('Пользовательский интерес:')
                user_interests()
                print('Сторонний сегмент:')
                other_segments()

            text = opened_file('interests').read().decode('ANSI')
            mass = re.findall('''item__main'>([А-яA-z0-9/ -–—,.()]+)</div>|item__tertiary'>([А-я ]+)</div>''', text)
            mass = list(map(lambda x: ''.join(x), mass))
            d = collections.defaultdict(list)
            [d[mass[i + 1]].append(mass[i]) for i in range(len(mass) - 1)]

            ads_interests_print_modes = list(enumerate(['Пользовательский интерес',
                                                        'Сторонний сегмент',
                                                        'Оба варианта']))
            ads_interests_mode_selectors = {0: user_interests, 1: other_segments, 2: all_interests}

            [print(f"{i[0]}: {i[1]}") for i in ads_interests_print_modes]
            ads_interests_mode_selectors[int(input('Выберите класс: '))]()

        def ads_all():
            print()
            ads_cord()
            print()
            ads_interests()

        ads_print_mode = list(enumerate(['Координаты',
                                         'Интересы',
                                         'Все режимы']))
        [print(f"{i[0]}: {i[1]}") for i in ads_print_mode]
        ads_mode_selector = {0: ads_cord, 1: ads_interests, 2: ads_all}
        ads_mode_selector[int(input('Выберите режим: '))]()


    def apps():
        pass


    ####################################################################################################################
    path = [i.filename for i in zp.infolist() if not i.is_dir()]  # Составляем список файлов
    mask = r'(?:\.\w+)?/.+|^(?:\w+\.\w+)$'
    modes = list(enumerate(sorted(set(re.sub(mask, '', i) for i in path if
                                      re.sub(mask, '', i)))))  # Создаем список папок и проверяем не пустое ли имя
    dmodes = dict(modes)  # Создаем словарь с папками
    [print(f"{i[0]}: {i[1]}") for i in modes]

    funcs = {0: ads, 1: apps}
    funcs[int(input('Выборите данные с которыми хотите работать: '))]()
