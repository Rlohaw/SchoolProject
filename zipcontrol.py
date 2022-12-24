import csv
from inspect import getfullargspec

from skelet import *


class ZipControl:
    __categories = dict(
        enumerate((Coordinates, Ads, Apps, Audios, Likes, Users, Messages, Others, Payments, Photos,
                   Profile, Video, Wall)))  # Нумерация функций

    def __init__(self, path):
        self.path = path.strip('\\')
        [print(k, v.__name__) for k, v in self.__categories.items()]
        self.category = self.__categories[int(input('Class: '))]  # Вывод функций, а так же выбор её

    @staticmethod
    def get(ex, dct):  # Функция для ввода аргументов в функцию
        f = getattr(ex, dct[int(input("Method: "))])
        sp = getfullargspec(f).args[1:]
        if sp:
            return f(input(f"{sp[0]}: "))
        return f()

    def select_data(self):  # Функция для выбора круга поиска сообщений
        users = dict(enumerate([i for i in dir(Users) if not i.startswith('_')]))
        [print(k, v) for k, v in users.items()]
        selected_users = users[int(input("Users: "))]
        args = getfullargspec(getattr(Users, selected_users)).args[1:]
        if args:
            return getattr(Users(self.path), selected_users)(input(f"{args[0]}: "))
        return getattr(Users(self.path), selected_users)()

    def start(self):  # Функция управляющая вводом - выводом
        sp = getfullargspec(self.category).args[2:]
        if not sp:
            exemplar = self.category(self.path)
            mode_dct = dict(enumerate([i for i in dir(exemplar) if not i.startswith('_')]))
            [print(k, v) for k, v in mode_dct.items()]
            return self.get(exemplar, mode_dct)
        else:
            exemplar = self.category(self.path, self.select_data())
            mode_dct = dict(enumerate([i for i in dir(exemplar) if not i.startswith('_')]))
            [print(k, v) for k, v in mode_dct.items()]
            return self.get(exemplar, mode_dct)


while True:
    try:
        archive = input('Archive: ')
        w = r'(\w+)'
        with open(f"archive-{re.findall(rf'{w}.zip', archive)[0]}.csv", 'w', encoding='cp1251', newline='') as file:
            a = ZipControl(archive)
            res = a.start()
            for s in res:
                s = '; '.join(map(lambda x: ': '.join(map(str, x)), s.items()))
                print(s)
            writer = csv.DictWriter(file, fieldnames=list(res[0].keys()) if isinstance(res, list) else list(res.keys()),
                                    delimiter=';', quotechar=';')
            writer.writeheader()
            if isinstance(res, list):
                [writer.writerow(i) for i in res]
            else:
                writer.writerow(res)
    except Exception as e:
        print(f'No data: {e}')
