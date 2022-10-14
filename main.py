import collections
import datetime
import locale
import re
import zipfile
from time import perf_counter

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


class Zip:
    def __init__(self, name):
        self.zip = zipfile.ZipFile(name)
        self.path = tuple((i.filename for i in self.zip.infolist() if not i.is_dir()))
        self.directory = name

    def __del__(self):
        self.zip.close()

    def get_text(self, key):
        text = self.read_file(key)
        text_dict = dict(map(lambda x: reversed(x), re.findall('<a href="(.*)">(.*)</a>', text)))
        return text_dict

    def read_file(self, key):
        try:
            with self.zip.open(*(i for i in self.path if key in i)) as file:
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


class Message:
    def __init__(self, id, name, date, type, link, text):
        self.id = id
        self.name = name
        self.type = type
        self.link = link
        self.text = text
        if 'мая' in date:
            date = date.replace('мая', 'май')
        self.date = datetime.datetime.strptime(date, '%d %b %Y в %H:%M:%S')

    def get_all(self):
        return tuple(filter(lambda x: bool(x), self.__dict__.values()))


class Messages(Zip):
    def __init__(self, name, work_dict):
        super().__init__(name)
        self.work_dict = work_dict

    def __iter__(self):
        for i in self.work_dict.values():
            num = 0
            while rf"messages/{i}/messages{num}.html" in self.path:
                res = self.read_file(rf"messages/{i}/messages{num}.html")
                num += 50
                mass = re.finditer(
                    r"""header">(?:<a href="(?P<id>.+)">)?(?P<name>.+)(?(id)</a>, |, )(?P<date>[А-я0-9 :]+).*\n(?:(?:(?:\s+.*\n){3}.*>(?P<type>[А-я0-9]+).*\n.*href='(?P<link>.*)'>)|  <div>(?P<text>.+)<div class="kludges">)""",
                    res)
                mass = list(map(lambda x: Message(*x.groupdict().values()), mass))
                yield from mass

    def file_messages(self):
        for msg in self:
            if msg.link is not None:
                yield msg

    def text_messages(self):
        for msg in self:
            if msg.text is not None:
                yield msg

    def search_by_words(self, wrong_words):
        return tuple(
            sp.get_all() for sp in self.text_messages() for ww in wrong_words if ww.lower() in sp.text.lower())

    def top_words(self, num):
        res = {}
        for i in self:
            if i.text is not None:
                res[i.text] = res.get(i.text, 0) + 1
        res = sorted(res.items(), key=lambda x: x[1], reverse=True)[0:num]
        return res

    def kd(self):
        m = 0
        nm = 0
        for i in self.text_messages():
            if i.name == 'Вы':
                m += len(re.findall(r'(\w+)', i.text))
            else:
                nm += len(re.findall(r'(\w+)', i.text))
        return round(m / nm, 2)


test = Messages(r'D:\sec\archive.zip', Users(r'D:\sec\archive.zip').get_persons())
start = perf_counter()
print(test.kd())
end = perf_counter()
print(end - start)
