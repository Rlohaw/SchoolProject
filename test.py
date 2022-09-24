import re
def read_file(key):
    with zp.open(*(i for i in path if key.lower() in i.lower())) as file:
        return file.read().decode('ANSI')

class ads():  # раздел рекламы
    def ads_cord():  # раздел частая геопозиция
        text = read_file('geo-points')
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

        text = read_file('interests')
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