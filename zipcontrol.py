from skelet import *
from inspect import getfullargspec


class ZipControl:
    __categories = dict(
        enumerate((Coordinates, Ads, Apps, Audios, Likes, Users, Messages, Others, Payments, Photos,
                   Profile, Video, Wall)))

    def __init__(self, zip_path):
        self.zip_path = zip_path.rstrip('\\')
        [print(k, v.__name__) for k, v in self.__categories.items()]
        self.category = self.__categories[int(input('Выберите категорию: '))]

    def selector(self):
        exemplar = self.category(self.zip_path)
        mode_dct = dict(enumerate([i for i in dir(exemplar) if not i.startswith('_')]))
        [print(k, v) for k, v in mode_dct.items()]
        argsa = getfullargspec(getattr(self.category, __init__))
        argsb = getfullargspec(getattr(exemplar, mode_dct[int(input("Выберите режим: "))])).args.remove('self')
        print(argsb)

archive = r'D:\sec\archive.zip'
while True:
    a = ZipControl(r'D:\sec\archive.zip')
    a.selector()





