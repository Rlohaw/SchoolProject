import collections
import re
import zipfile


class Zip:
    def __init__(self, name):
        self.__zip = zipfile.ZipFile(name)
        self.path = tuple((i.filename for i in self.__zip.infolist() if not i.is_dir()))

    def __del__(self):
        self.__zip.close()

    def get_text(self, key):
        text = self.read_file(key)
        text_dict = dict(map(lambda x: reversed(x), re.findall('<a href="(.*)">(.*)</a>', text)))
        return text_dict

    def read_file(self, key):
        try:
            with self.__zip.open(*(i for i in self.path if key in i)) as file:
                return file.read().decode('ANSI')
        except TypeError:
            pass


class Coordinates(Zip):
    def __init__(self, name):
        super().__init__(name)
        text = self.read_file('geo-points')
        self.__coordinates = re.search('<a href="(?P<Coodrinates_site>.+)">'
                                       '(?P<latitude>.+), '
                                       '(?P<longitude>.+)</a>',
                                       text).groupdict()

    def get_coordinates(self):
        return self.__coordinates


class Ads(Zip):
    def __init__(self, name):
        super().__init__(name)
        text = self.read_file('interests')
        mass = re.findall('''item__main'>(.+)</div>|item__tertiary'>(.+)</div>''', text)
        mass = list(map(lambda x: ''.join(x), mass))
        self.__ads = collections.defaultdict(list)
        [self.__ads[mass[i + 1]].append(mass[i]) for i in range(0, len(mass), 2)]

    def get_ads_personal_interest(self):
        return self.__ads['Пользовательский интерес']

    def get_ads_system(self):
        return self.__ads['Системный сегмент']

    def get_ads_other(self):
        return self.__ads['Сторонний сегмент']

    def get_ads(self):
        return self.get_ads_personal_interest() + self.get_ads_system() + self.get_ads_other()


class Apps(Zip):
    def __init__(self, name):
        super().__init__(name)
        self.__apps = re.findall("class='item__main'>(.+)</div>", self.read_file('apps'))

    def get_apps(self):
        return self.__apps


class Audios(Zip):
    def __init__(self, name):
        super().__init__(name)
        self.__audios = collections.defaultdict(set)
        for nam in self.get_text('audio-albums.html').values():
            if self.read_file(nam):
                text = self.read_file(nam)
                mass = re.findall('audio__title">(?P<name>.+) &mdash; (?P<artist>.+)</div>', text)
                [self.__audios[i[0]].update([i[1]]) for i in mass]

    def get_audios(self):
        return self.__audios


class Bookmarks(Zip):
    def __init__(self, name):
        super().__init__(name)
        self.__bookmarks = collections.defaultdict(set)
        for nam in self.get_text('audio-albums.html').values():
            if self.read_file(nam):
                text = self.read_file(nam)
                mass = re.findall('audio__title">(?P<name>.+) &mdash; (?P<artist>.+)</div>', text)
                [self.__bookmarks[i[0]].update([i[1]]) for i in mass]

    def get_bookmarks(self):
        return self.__bookmarks


class Likes(Zip):
    def __init__(self, name):
        super().__init__(name)
        self.__likes = collections.defaultdict(list)
        for key, nam in self.get_text('likes.html').items():
            if self.read_file(nam):
                text = self.read_file(nam)
                mass = re.findall('<a href="(.*)">', text)
                self.__likes[key].extend(mass)

    def get_likes(self):
        return self.__likes



