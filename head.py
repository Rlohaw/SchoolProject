import re

from skelet import *
import csv
categories = dict(enumerate((Coordinates, Ads, Apps, Audios, Bookmarks, Likes, Users, Messages, Others, Payments, Photos,
                      Profile, Video, Wall)))
while True:
    [print(k, v.__name__) for k, v in categories.items()]
    category = int(input('Выберите категорию: '))
    work_category = categories[category]
    archive = input('Укажите абсолютный путь к архиву: ').rstrip('\\')
    if work_category != Messages:
        exemplar_of_category = work_category(archive)
        mode_dct = dict(enumerate([i for i in dir(exemplar_of_category) if not i.startswith('_')]))
        [print(k, v) for k, v in mode_dct.items()]
        res = getattr(exemplar_of_category, mode_dct[int(input("Выберите режим: "))])()
    else:
        users = dict(enumerate([i for i in dir(Users) if not i.startswith('_')]))
        [print(k, v) for k, v in users.items()]
        selected_users = users[int(input("Выберите категорию пользователей: "))]
        if selected_users != 'get_one':
            exemplar_of_category = work_category(archive, getattr(Users, selected_users)())
            mode_dct = dict(enumerate([i for i in dir(Messages) if not i.startswith('_')]))
            [print(k, v) for k, v in mode_dct.items()]
            res = getattr(exemplar_of_category, mode_dct[int(input('Выберите режим: '))])()
            print(res)
    break