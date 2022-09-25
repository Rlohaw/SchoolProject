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
        except TypeError:
            pass


    def get_text(key):
        text = read_file(key)
        text_dict = dict(map(lambda x: reversed(x), re.findall('<a href="(.*)">(.*)</a>', text)))
        return text_dict


    def time_counter(f):  # Отладка по времени(декоратор)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            a = f(*args, **kwargs)
            end = time.perf_counter()
            print(end - start, 'c')
            return a

        return wrapper


    def print_enumerated_modes(mode):
        [print(f"{i[0]}: {i[1]}") for i in mode]


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

            ads_interests_mode_selectors = {0: user_interests, 1: other_segments, 2: system_segment, 3: all_interests}
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
        def album_sort():
            d = collections.defaultdict(set)
            for nam in get_text('audio-albums.html').values():
                if read_file(nam):
                    text = read_file(nam)
                    mass = re.findall('audio__title">(?P<name>.+) &mdash; (?P<artist>.+)</div>', text)
                    [d[i[0]].update([i[1]]) for i in mass]
            d = sorted(d.items(), key=lambda x: len(x[1]), reverse=True)
            [print(f"{i[0]}: {', '.join(sorted(i[1]))}") for i in d]

        album_sort()


    def bookmarks():

        def bookmarks_sort():
            d = collections.defaultdict(list)
            for key, nam in get_text('bookmarks.html').items():
                if read_file(nam):
                    text = read_file(nam)
                    mass = re.findall('<a href="(.*)">', text)
                    d[key].extend(mass)
            [print(f"{i[0]}: {', '.join(i[1])}") for i in d.items() if i[1]]

        bookmarks_sort()


    def likes():
        def likes_sort():
            d = collections.defaultdict(list)
            for key, nam in get_text('likes.html').items():
                if read_file(nam):
                    text = read_file(nam)
                    mass = re.findall('<a href="(.*)">', text)
                    d[key].extend(mass)
            return d

        likes_modes = dict(enumerate([*(i[0] for i in likes_sort().items() if i[1]), 'Все варианты']))
        print_enumerated_modes(list(likes_modes.items()))
        n = int(input())
        s = '\n'
        m = map(lambda x: rf"{x[0]}:{s}{s.join(x[1])}{s}" if x[1] else f"{x[0]}: Пусто{s}", likes_sort().items())
        print(*likes_sort()[likes_modes[n]] if n != list(likes_modes.keys())[-1] else m, sep='\n')


    def messages():
        def messaages_users_select():
            messages_users_dict = list(get_text('index-messages.html').items())

            def groups():
                res = dict([(i[0], re.search('([0-9-]+)/', i[1]).group(1)) for i in messages_users_dict if
                            i[1].startswith('-')])
                return res

            def persons():
                res = dict([(i[0], re.search('([0-9-]+)/', i[1]).group(1)) for i in messages_users_dict if
                            re.search('^(\d{3,9}/)', i[1])])
                return res

            def chats():
                res = dict([(i[0], re.search('([0-9-]+)/', i[1]).group(1)) for i in messages_users_dict if
                            re.search('^(\d{10}/)', i[1])])
                return res

            def every():
                res = dict([(i[0], re.search('([0-9-]+)/', i[1]).group(1)) for i in messages_users_dict])
                return res

            def one():
                try:
                    user = input('Имя пользователя: ')
                    value = every()[user]
                    return {user: value}
                except KeyError:
                    print('Нет такого пользователя')
                    return one()

            print_enumerated_modes(enumerate(['Группы', 'Пользователи', 'Беседы', 'Один пользователь']))
            d = {0: groups, 1: persons, 2: chats, 3: one}
            print(d)
            return one()

        print(messaages_users_select())


    ###############################################################################################################
    path = [i.filename for i in zp.infolist() if not i.is_dir()]  # Составляем список файлов
    mask = r'(?:\.\w+)?/.+|^(?:\w+\.\w+)$'
    modes = list(enumerate(sorted(set(re.sub(mask, '', i) for i in path if
                                      re.sub(mask, '', i)))))  # Создаем список папок и проверяем не пустое ли имя
    print_enumerated_modes(modes)
    funcs = {0: ads, 1: apps, 2: audios, 3: bookmarks, 4: likes, 5: messages}
    funcs[int(input('Выберите данные с которыми хотите работать: '))]()
