import collections
import locale
import re
import zipfile
from time import perf_counter

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


class Zip:
    def __init__(self, name):
        self.__zip = zipfile.ZipFile(name)
        self.path = tuple((i.filename for i in self.__zip.infolist() if not i.is_dir()))
        self.directory = name

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


class Users(Zip):
    def __init__(self, name):
        super().__init__(name)
        self.__messages_users = tuple(self.get_text('index-messages.html').items())

    def get_groups(self):
        res = dict([(i[0], re.search('([0-9-]+)/', i[1]).group(1)) for i in self.__messages_users if
                    i[1].startswith('-')])
        return res

    def get_persons(self):
        res = dict([(i[0], re.search('([0-9-]+)/', i[1]).group(1)) for i in self.__messages_users if
                    re.search(r'^(\d{3,9}/)', i[1])])
        return res

    def get_chats(self):
        res = dict([(i[0], re.search('([0-9-]+)/', i[1]).group(1)) for i in self.__messages_users if
                    re.search(r'^(\d{10}/)', i[1])])
        return res

    def get_every(self):
        res = dict([(i[0], re.search('([0-9-]+)/', i[1]).group(1)) for i in self.__messages_users])
        return res

    def get_one(self, person_name):
        value = self.get_every()[person_name]
        return {person_name: value}


class Message(Zip):
    def __init__(self, name, work_dict):
        super().__init__(name)
        self.work_dict = work_dict

    def __iter__(self):
        for i in self.work_dict.values():
            num = 0
            while rf"messages/{i}/messages{num}.html" in self.path:
                res = self.read_file(rf"messages/{i}/messages{num}.html")
                num += 50
                mass = re.findall(
                    r""">(?:<a href=)?"?(?P<id>[A-z:/\.0-9]+)?(?:">)?(?P<name>(?:\w| )+)(?:</a>)?, (?P<date>[А-я0-9 :]+).*$\n(?:(?:(?:^\s+.*\n){3}.*>(?P<type>[А-я0-9]+).*\n.*href='(?P<link>.*)</a>)|  <div>(?P<text>.+)<div class="kludges">)""",
                    res)
                yield mass

    def get_words(self):
        for i in self:
            res = i

test = Message(r'D:\sec\archive.zip', Users(r'D:\sec\archive.zip').get_every())
start = perf_counter()
res = test.get_words()
end = perf_counter()
print(end - start)
# <div class="message__header">(?:<a href=)?"?(?P<id>[A-z:/\.0-9]+)?(?:">)?(?P<name>(?:\w| )+)(?:</a>)?, (?P<date>[А-я0-9 :]+)</div>\n  <div>(?P<text>.+)<div class="kludges">', res)
