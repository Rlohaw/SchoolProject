import collections
import datetime
import locale
import re
import zipfile

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

    def get_paths_by_key(self, key):
        return [i for i in self.path if key in i]


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
    def __init__(self, id, name, date, type, link, text, filename):
        self.id = id
        self.name = name
        self.type = type
        self.link = link
        self.text = text
        if 'мая' in date:
            date = date.replace('мая', 'май')
        self.date = datetime.datetime.strptime(date, '%d %b %Y в %H:%M:%S')
        self.filename = filename

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
                filename = rf"messages/{i}/messages{num}.html"
                num += 50
                mass = re.finditer(
                    r"""header">(?:<a href="(?P<id>.+)">)?(?P<name>.+)(?(id)</a>, |, )(?P<date>[А-я0-9 :]+).*\n(?:(?:\s+.*\n){3}.*>(?P<type>[А-я0-9]+).*\n.*href='(?P<link>.*)'>| {2}<div>(?P<text>.+)<div class="kludges">)""",
                    res)
                mass = list(map(lambda x: Message(*x.groupdict().values(), filename), mass))
                yield from mass

    def file_messages(self):
        for msg in self:
            if msg.link is not None:
                yield msg

    def text_messages(self):
        for msg in self:
            if msg.text is not None:
                yield msg

    def search_by_words(self, words):
        return tuple(
            sp.get_all() for sp in self.text_messages() for ww in words if ww.lower() in sp.text.lower())

    def get_top_words(self, num):
        res = {}
        for i in self:
            if i.text is not None:
                res[i.text] = res.get(i.text, 0) + 1
        res = sorted(res.items(), key=lambda x: x[1], reverse=True)[0:num]
        return res

    def get_kd(self):
        m = 0
        nm = 0
        for i in self.text_messages():
            if i.name == 'Вы':
                m += len(re.findall(r'(\w+)', i.text))
            else:
                nm += len(re.findall(r'(\w+)', i.text))
        return round(m / nm, 2)

    def get_total_words(self):
        return sum(len(re.findall(r'(\w+)', i.text)) for i in self.text_messages())


class Others(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_contacts(self):
        res = [j for i in self.get_paths_by_key('other/external-contacts/archive') for j in
               re.findall("'item__main'>(?P<value>.*)</div>", self.read_file(i))]
        return res

    def get_bans(self):
        bans = re.findall(r"'item__tertiary'>(?P<value>.*)</div>", self.read_file('bans.html'))
        for i in range(len(bans)):
            if 'мая' in bans[i]:
                bans[i] = bans[i].replace('мая', 'май')
            bans[i] = datetime.datetime.strptime(bans[i], '%d %b %Y в %H:%M')
        return bans


class Payments(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_cards(self):
        return re.findall("'item__main'>(?P<value>.*)</div>", self.read_file('cards-info'))

    def get_money_transfer(self):
        mass = re.findall(
            """'item__main'>(?P<trans>.+)</div><div.+'item__main'>(?P<operator>.+)<.* {2} {2}.+tertiary'>(?P<date>.+)<""",
            self.read_file('payments-history'))
        mass = list(map(list, mass))
        res = {}
        for i in range(len(mass)):
            if 'мая' in mass[i][2]:
                mass[i][2] = mass[i][2].replace('мая', 'май')
            res[datetime.datetime.strptime(mass[i][2], '%d %b %Y в %H:%M')] = [mass[i][0], mass[i][1]]
        return res

    def get_votes(self):
        mass = re.findall(
            r"""'item__main'>(.+)</div><div.+'item__main'>(.+).*<a href="(.*)" c.*>(.*)</a></div>\n {2}\n {2}.+tertiary'>(.+)<|'item__main'>(.+)</div><div.+'item__main'>(.+)</div>\n {2}\n {2}.+tertiary'>(.+)<""",
            self.read_file('/votes-history'))
        res = [list(filter(bool, i)) for i in mass]
        fin = {}
        for i in range(len(res)):
            if 'мая' in res[i][-1]:
                res[i][-1] = res[i][-1].replace('мая', 'май')
            res[i][-1] = datetime.datetime.strptime(res[i][-1], '%d %b %Y в %H:%M')
            fin[res[i][-1]] = res[i][0:-1]
        return fin


class Photos(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_photos(self):
        sp = []
        for i in self.get_paths_by_key('photos'):
            sp.extend(re.findall('src="(.+)" ', self.read_file(i)))
        return list(filter(bool, sp))


class Profile(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_blacklist(self):
        sp = {}
        for i in map(list, re.findall(r"""href="(.+)" .*">(.+)</a></div>\n\s\s\n.*'>(.+)</div>""",
                                      self.read_file('blacklist'))):
            if 'мая' in i[2]:
                i[2] = i[2].replace('мая', 'май')
            i[2] = datetime.datetime.strptime(i[2], '%d %b %Y в %H:%M')
            sp[i[0]] = i[1:]
        return sp

    def get_documents(self):
        return re.findall('<a href="(.*)"', self.read_file('documents'))

    def get_emails(self):
        return re.findall(r"main'>(\S+).*</div>", self.read_file('email-changes'))

    def get_requests(self):
        return re.findall('href="(.+)">(.*)</a><', self.read_file('friends-requests'))

    def get_friends(self):
        return re.findall('href="(.+)">(.*)</a><', self.read_file('friends0.html'))

    def get_names(self):
        return {j for i in re.findall("main'>.+имени (.+) на (.+)</div>", self.read_file('name-changes')) for j in i}

    def get_page_info(self):
        mass = re.findall(
            r"""">(.+)(?:</div>\s{3}|</div><div>)(?:<div>.*"(.+)" c|<div>(.*)</div>|(.*)<.div>)""",
            self.read_file('page-info'))
        return {a: b if b else c if c else d for a, b, c, d in mass if
                b != 'Данных нет' and c != 'Данных нет' and d != 'Данных нет'}

    def get_phones(self):
        return {i for i in re.findall(r"main'>.* (\d+).*</div>", self.read_file('phone-changes'))}

    def get_stories(self):
        return re.findall('href="(.+)">vk', self.read_file('stories'))

    def get_subs(self):
        return re.findall('href="(.+)">(.*)</a></div>', self.read_file('subscriptions0.html'))


class Video(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_videos(self):
        res = []
        for i in self.get_paths_by_key('video-albums'):
            res.extend(re.findall('<a href="(.*)">\n', self.read_file(i)))
        return res


class Wall(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_wall(self):
        res = []
        for i in self.get_paths_by_key('wall'):
            res.extend(re.findall('<a class="post__link fl_l" href="(.*)">', self.read_file(i)))
        return res
