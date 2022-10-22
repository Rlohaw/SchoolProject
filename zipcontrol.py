import csv
from inspect import getfullargspec

from skelet import *


class ZipControl:
    __categories = dict(
        enumerate((Coordinates, Ads, Apps, Audios, Likes, Messages, Others, Payments, Photos,
                   Profile, Video, Wall)))

    def __init__(self, path):
        self.path = path.strip('\\')
        [print(k, v.__name__) for k, v in self.__categories.items()]
        self.category = self.__categories[int(input('Class: '))]

    def get(self, ex, dct):
        f = getattr(ex, dct[int(input("Method: "))])
        sp = getfullargspec(f).args[1:]
        if sp:
            return f(input(f"{sp[0]}: "))
        return f()

    def select_data(self):
        users = dict(enumerate([i for i in dir(Users) if not i.startswith('_')]))
        [print(k, v) for k, v in users.items()]
        selected_users = users[int(input("Users: "))]
        args = getfullargspec(getattr(Users, selected_users)).args[1:]
        if args:
            return getattr(Users(self.path), selected_users)(input(f"{args[0]}: "))
        return getattr(Users(self.path), selected_users)()

    def start(self):
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


archive = input("Archive: ")
w = r'(\w+)'
with open(f"archive-{re.findall(rf'{w}.zip', archive)[0]}.csv", 'w', encoding='utf-8', newline='') as file:
    while True:
        try:
            a = ZipControl(archive)
            res = a.start()
            print(res)
            writer = csv.DictWriter(file, fieldnames=list(res[0].keys()) if isinstance(res, list) else list(res.keys()))
            writer.writeheader()
            if isinstance(res, list):
                [writer.writerow(i) for i in res]
            else:
                writer.writerow(res)
        except Exception as e:
            print(e)
