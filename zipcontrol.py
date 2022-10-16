from skelet import *


class ZipControl:
    __categories = dict(
        enumerate((Coordinates, Ads, Apps, Audios, Bookmarks, Likes, Users, Messages, Others, Payments, Photos,
                   Profile, Video, Wall)))

    def __init__(self, zip_path):
        self.zip_path = zip_path.rstrip('\\')
        [print(k, v.__name__) for k, v in self.__categories.items()]
        self.category = self.__categories[int(input('Выберите категорию: '))]

    def normal(self):
        exemplar = self.category(self.zip_path)
        mode_dct = dict(enumerate([i for i in dir(exemplar) if not i.startswith('_')]))
        [print(k, v) for k, v in mode_dct.items()]
        return getattr(exemplar, mode_dct[int(input("Выберите режим: "))])()

    def msg(self):
        users = dict(enumerate([i for i in dir(Users) if not i.startswith('_')]))
        [print(k, v) for k, v in users.items()]
        selected_users = users[int(input("Выберите круг лиц: "))]
        mode_dct = dict(enumerate([i for i in dir(Messages) if not i.startswith('_')]))
        if selected_users != 'get_one':
            [print(k, v) for k, v in mode_dct.items()]
            exemplar = self.category(self.zip_path, getattr(Users(self.zip_path), selected_users)())
            selected_mode = mode_dct[int(input("Выберите режим: "))]
            if selected_mode != 'search_by_words':
                return getattr(exemplar, selected_mode)
            else:
                return getattr(exemplar, selected_mode)(input('Ведите фрагмент текста: ').split())
        else:
            exemplar = self.category(self.zip_path, getattr(Users(self.zip_path), selected_users)(input('Ведите лицо: ')))
            [print(k, v) for k, v in mode_dct.items()]
            selected_mode = mode_dct[int(input("Выберите режим: "))]
            if selected_mode != 'search_by_words':
                return getattr(exemplar, selected_mode)
            else:
                return getattr(exemplar, selected_mode)(input('Ведите фрагмент текста: ').split())





