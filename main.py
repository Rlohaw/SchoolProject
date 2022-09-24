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


    def read_file(key):
        try:
            with zp.open(*(i for i in path if key in i)) as file:
                return file.read().decode('ANSI')
        except TypeError as e:
            return None


    def time_counter(f):  # Отладка по времени(декоратор)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            a = f(*args, **kwargs)
            end = time.perf_counter()
            print(end - start, 'c')
            return a

        return wrapper

    def print_enumerated_modes(modes):
        [print(f"{i[0]}: {i[1]}") for i in modes]
    def ads():  # раздел рекламы
        def ads_cord():  # раздел частая геопозиция
            text = read_file('geo-points')
            geo = re.search('<a href="(?P<site>.+)">(?P<lat>.+), (?P<lon>.+)</a>', text)
            print(f"Геопозиция на картах:{geo['site']}\n{geo['lat']}\n{geo['lon']}")

        def ads_interests():  # раздел интересы
            def user_interests():
                print(*d['Пользовательский интерес'], sep='\n')

            def other_segments():
                print(*d['Сторонний сегмент'], sep='\n')

            def system_segment():
                print(*d['Системный сегмент'], sep='\n')

            def all_interests():
                user_interests()
                other_segments()
                system_segment()

            text = read_file('interests')
            mass = re.findall('''item__main'>([А-яA-z0-9/ -–—,.()]+)</div>|item__tertiary'>([А-я ]+)</div>''', text)
            mass = list(map(lambda x: ''.join(x), mass))
            d = collections.defaultdict(list)
            [d[mass[i + 1]].append(mass[i]) for i in range(0, len(mass), 2)]

            ads_interests_print_modes = list(enumerate([*d.keys(), 'Оба варианта']))
            print_enumerated_modes(ads_interests_print_modes)

            ads_interests_mode_selectors = {0: user_interests, 1: other_segments, 2: system_segment, 3:all_interests}
            ads_interests_mode_selectors[int(input('Выберите класс: '))]()

        def ads_all():
            print()
            ads_cord()
            print()
            ads_interests()

        ads_print_modes = list(enumerate(['Координаты',
                                         'Интересы',
                                         'Все режимы']))
        ads_mode_selector = {0: ads_cord, 1: ads_interests, 2: ads_all}

        print_enumerated_modes(ads_print_modes)
        ads_mode_selector[int(input('Выберите режим: '))]()


    def apps():
        text = re.findall("class='item__main'>([A-zА-я -]+)</div>", read_file('apps'))
        print(*text, sep='\n')


    def audios():
        def get_albums():
            text = read_file('audio-albums.html')
            albums_dict = dict(map(lambda x: reversed(x), re.findall('<a href="(?P<path>.*)">(?P<name>.*)</a>', text)))
            return albums_dict

        def album_sort():
            d = collections.defaultdict(set)
            for name in get_albums().values():
                if read_file(name):
                    text = read_file(name)
                    mass = re.findall('audio__title">(?P<name>.+) &mdash; (?P<artist>.+)</div>', text)
                    [d[i[0]].update([i[1]]) for i in mass]
            [print(f"{i[0]}: {', '.join(sorted(i[1]))}") for i in d.items()]

        album_sort()



    ####################################################################################################################
    path = [i.filename for i in zp.infolist() if not i.is_dir()]  # Составляем список файлов
    mask = r'(?:\.\w+)?/.+|^(?:\w+\.\w+)$'
    modes = list(enumerate(sorted(set(re.sub(mask, '', i) for i in path if
                                      re.sub(mask, '', i)))))  # Создаем список папок и проверяем не пустое ли имя
    print_enumerated_modes(modes)
    funcs = {0: ads, 1: apps, 2: audios}
    funcs[int(input('Выберите данные с которыми хотите работать: '))]()
