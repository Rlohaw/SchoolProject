import locale
import time
from datetime import datetime
import zipfile
import re

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
name = input('Archive Path: ').strip()
if not name.endswith('.zip'):
    name+='.zip'

with zipfile.ZipFile(name, mode='r') as zp:
    path = [i.filename for i in zp.infolist() if not i.is_dir()]
    modes = '\n'.join(sorted(set(i.split('/', 1)[0] for i in path if '.' not in i.split('/', 1)[0])))

    mode = input('\nDATA SETS:\n'+modes+'\nSELECT: ').strip()
    filtred_files = list(filter(lambda x:x.split('/', 1)[0] == mode, path))

    if mode == 'ads':

        def ads_cord():
            for i in filtred_files:
                if 'geo-points' in i:
                    with zp.open(i) as vrfl:
                        pr = vrfl.read().decode('windows-1251', "ignore")
                        pr = [i.replace('\n\n', '') for i in pr.split()]
                        GM = list(filter(lambda x: 'google' in x, pr))[0].replace('href="','').replace('">:','').replace('">Широта','')
                        cord = GM[GM.index('=')+1:].replace('">Широта','').split(',')
                        print(f'\nPopular place:\nCoordinates: {", ".join(cord)}\nGoogle Maps: {GM}\n')
                        break

        def ads_interests():
            for i in filtred_files:
                if 'interests' in i:
                    with zp.open(i) as vrfl:
                        pr = vrfl.read().decode('windows-1251', "ignore")
                        text = pr.split('</h2><div class="wrap_page_content">\n  <div class="item">\n')[1].replace('\n  \n  ', '\n').split('</div>\n</div>\n<!--/content-->')[0].rstrip('\n')
                        mass = [[i.lstrip().split('\n')[0].split("<div class='item__main'>")[1].rstrip('</div>'), i.lstrip().split('\n')[1].split("<div class='item__tertiary'>")[1].rstrip('</div>')][::-1] for i in text.split('\n</div><div class="item">\n')]
                        dc = {}
                        for i in mass:
                            dc[i[0]] = dc.get(i[0],'') + i[1]+'\n'
                        q = input('\nChoose Category:\nui: User Interests\nos: Other Segment\nall: All Categories\nSELECT: ').strip()
                        sl = {'ui': 'Пользовательский интерес', 'os': 'Сторонний сегмент', 'all': False}
                        if sl[q]:
                            print(dc[sl[q]])
                        else:
                            print(f'\nПользовательский интерес:\n{dc["Пользовательский интерес"]}\nСторонний сегмент:\n{dc["Сторонний сегмент"]}')
                        break

        chs = input('\nACTIONS:\ncrd: Coordinates\nint: Interests\nSELECT: ').strip()
        if chs == 'crd':
            ads_cord()
        elif chs == 'int':
            ads_interests()

    elif mode == 'apps':
        for i in filtred_files:
            if 'apps' in i:
                with zp.open(i) as vrfl:
                    pr = vrfl.read().decode('windows-1251', "ignore")
                    text = pr.split('</h2><div class="wrap_page_content">\n  <div class="item">\n')[1].split('</div>\n</div>\n<!--/content-->')[0].rstrip('\n')
                    md = input("\nShow applications? y/n: ")
                    mass = [[i.lstrip().split('\n')[0].split("<div class='item__main'>")[1].rstrip('</div>'), i.split('\n')[2].lstrip().lstrip("<div class='item__tertiary'>").split("</div><div class='item__tertiary'>Дата последнего запуска неизвестна</div>")[0]] for i in text.split('\n</div>\n<div class="item">\n')]
                    if md == 'y':
                        mass = list(map(lambda x: '\n'.join(x), mass))
                        print()
                        print(*mass, sep='\n\n')
                    elif md == 'n':
                        mass = list(map(lambda x:x[0], mass))
                        print(*mass, sep='\n')
                    break

    elif mode == 'audio':
        for i in filtred_files:
            if 'audios0' in i:
                with zp.open(i) as vrfl:
                    pr = vrfl.read().decode('windows-1251', "ignore")
                    print('Under Development')
    elif mode == 'bookmarks':
        print('Under Development')
    elif mode == 'likes':
        print('Under Development')

    # elif mode == 'messages':









