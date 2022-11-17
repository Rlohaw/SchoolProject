import collections
import datetime
import locale
import re
import time
import zipfile
from bs4 import BeautifulSoup

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


class Zip:
    def __init__(self, name):
        self.__zip = zipfile.ZipFile(name)
        self._path = tuple((i.filename for i in self.__zip.infolist() if not i.is_dir()))
        self.__directory = name

    def __del__(self):
        self.__zip.close()

    def _get_text(self, key):
        soup = BeautifulSoup(self._read_file(key), 'lxml')
        text_dict = {i.get_text(): i.get('href') for i in soup.find_all('a')}
        return text_dict

    def _read_file(self, key):
        try:
            with self.__zip.open(*(i for i in self._path if key in i)) as file:
                return file.read().decode('ANSI')
        except TypeError:
            pass

    def _get_paths_by_key(self, key):
        return [i for i in self._path if key in i]

    @staticmethod
    def _date_corrector(mass):
        res = []
        for i in mass:
            ex = i.groupdict()
            if 'мая' in ex['Date']:
                ex['Date'] = ex['Date'].replace('мая', 'май')
            res.append(ex)
        return sorted(res, key=lambda x: datetime.datetime.strptime(x['Date'], '%d %b %Y в %H:%M'))


class Coordinates(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_coordinates(self):
        soup = BeautifulSoup(self._read_file('geo-points'), 'lxml')
        a = soup.find(class_='item__main').find('a')
        mass = a.get_text('|;|', strip=True).split()[1::2]
        return [{'Link': a.get('href'), 'Latitude': mass[0], 'Longitude': mass[1]}]


class Ads(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_ads_personal_interest(self):
        return list(filter(lambda x: x['Type'] == 'Пользовательский интерес', self.get_ads()))

    def get_ads_system(self):
        return list(filter(lambda x: x['Type'] == 'Системный сегмент', self.get_ads()))

    def get_ads_other(self):
        return list(filter(lambda x: x['Type'] == 'Сторонний сегмент', self.get_ads()))

    def get_ads(self):
        soup = BeautifulSoup(self._read_file('interests'), 'lxml')
        res = ({'Interest': i.find(class_='item__main').get_text(), 'Type': i.find(class_='item__tertiary').text} for i
               in soup.find_all(class_='item'))
        return res


class Apps(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_apps(self):
        soup = BeautifulSoup(self._read_file('apps'), 'lxml')
        return ({'App': i.get_text()} for i in soup.find_all(class_='item__main'))


class Audios(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_audios(self):
        audios = []
        for nam in self._get_text('audio-albums.html').values():
            read = self._read_file(nam)
            if read:
                soup = BeautifulSoup(read, 'lxml')
                g = ({'Name': n, 'Artist': a} for a, n in
                     map(lambda x: x.get_text().split(' — '), soup.find_all(class_='audio__title')))
                audios.extend(g)
        return audios


class Likes(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_likes(self):
        likes = []
        for key, nam in self._get_text('likes.html').items():
            read = self._read_file(nam)
            if read:
                soup = BeautifulSoup(read, 'lxml')
                [likes.append({'Type': key, 'Url': i.get_text()}) for i in soup.find_all('a') if
                 i.get_text().startswith('https')]
        return sorted(likes, key=lambda x: x['Type'])


class Users(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_groups(self):
        res = list(filter(lambda x: x['MSGID'].startswith('-'), self.get_every()))
        return res

    def get_persons(self):
        res = list(filter(lambda x: 3 < len(x['MSGID']) < 10 and not x['MSGID'].startswith('-'), self.get_every()))
        return res

    def get_chats(self):
        res = list(filter(lambda x: len(x['MSGID']) == 10 and x['MSGID'].startswith('2'), self.get_every()))
        return res

    def get_every(self):
        soup = BeautifulSoup(self._read_file('index-messages.html'), 'lxml')
        res = ({'Name': k, 'MSGID': re.search(r'\d+', v).group()} for k, v in
               self._get_text('index-messages.html').items() if re.findall('\d+', v))
        return res

    def get_one(self, person_name):
        res = list(filter(lambda x: x['Name'] == person_name, self.get_every()))
        return res


class Messages(Zip):
    def __init__(self, name, _work_dict):
        super().__init__(name)
        self._work_dict = _work_dict

    def __iter__(self):
        for i in map(lambda x: x['MSGID'], self._work_dict):
            num = 0
            while rf"messages/{i}/messages{num}.html" in self._path:
                bs = BeautifulSoup(self._read_file(rf"messages/{i}/messages{num}.html"), 'lxml')
                num += 50
                text = filter(lambda x: len(x) > 1 if x[0].startswith('Вы, ') else len(x) > 2,
                              map(lambda x: x.get_text('||;||', strip=True).split('||;||')[0:3],
                                  bs.find_all(class_='message')))
                id = collections.Counter(map(lambda x: x.get('href'), bs.find_all('a'))).most_common(1)[0][0]
                ww = ('Видеозапись', 'Файл', 'Фотография', 'Сообщение удалено', 'Стикер', 'Запись со стены', 'Ссылка',
                      '(ред.)')
                yield from ({'Name': msg[0] if not msg[0].startswith('Вы, ') else 'Вы',
                             'Date': msg[0].lstrip('Вы, ') if msg[0].startswith('Вы, ') else msg[1],
                             'Text': msg[1] if msg[0].startswith('Вы, ') else msg[2],
                             'Id': id if msg[0].startswith('Вы, ') else 0} for msg in text if not
                            (msg[1] in ww if msg[0].startswith('Вы, ') else msg[2] in ww))

    def search_by_words(self, words_or_file):
        try:
            with open(words_or_file, encoding='utf-8') as file:
                file = [i.strip().lower() for i in file.readlines()]
                return sorted([sp for sp in self for ww in file if ww.lower() == sp['Text'].lower()],
                              key=lambda x: datetime.datetime.strptime(x['Date'], '%d %b %Y в %H:%M:%S'))
        except FileNotFoundError:
            return sorted([sp for sp in self if words_or_file.lower() in sp['Text'].lower()],
                          key=lambda x: datetime.datetime.strptime(x['Date'], '%d %b %Y в %H:%M:%S'))

    def get_top_words(self):
        return collections.Counter(i.lower() for j in self for i in re.findall(r'\w+', j['Text']))

    def get_kd(self):
        m = 0
        nm = 0
        for i in self:
            if i['Name'] == 'Вы':
                m += len(re.findall(r'(\w+)', i['Text']))
            else:
                nm += len(re.findall(r'(\w+)', i['Text']))
        return [{'Kd': round(m / nm, 2)}]

    def get_total_words(self):
        return [{'Words': collections.Counter(
            w.group() for msg in self for w in re.finditer(r'(\w+)', msg['Text'])).total()}]

    def get_messages(self):
        return sorted([i for i in self],
                      key=lambda x: datetime.datetime.strptime(x['Date'], '%d %b %Y в %H:%M:%S'))


class Others(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_contacts(self):
        res = [{'Number': j} for i in self._get_paths_by_key('other/external-contacts/archive') for j in
               re.findall("'item__main'>(.*)</div>", self._read_file(i))]
        return res

    def get_bans(self):
        bans = re.finditer(r"'item__tertiary'>(?P<Date>.*)</div>", self._read_file('bans.html'))
        return [i.groupdict() for i in bans]


class Payments(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_cards(self):
        n = re.finditer("'item__main'>(?P<Number>.*)</div>", self._read_file('cards-info'))
        return [i.groupdict() for i in n]

    def get_money_transfer(self):
        mass = re.finditer(
            r"""'item__main'>(?P<Transaction>.+)</div><div.+'item__main'>(?P<Operator>.+)<.*\s{4}.+tertiary'>(?P<Date>.+)<""",
            self._read_file('payments-history'))
        return self._date_corrector(mass)

    def get_votes(self):
        mass = re.finditer(
            r"""item__main'>(?P<Transaction>.+)</div>.+main'>(?:(?P<Present>.+) в подарок <a.+"(?P<Id>.+) class.+ >(?P<Name>.+)</a></div>|(?P<Item>.+)</div>)""",
            self._read_file('/votes-history'))
        return [i.groupdict() for i in mass]


class Photos(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_photos(self):
        sp = []
        for i in self._get_paths_by_key('photos'):
            sp.extend([i.groupdict() for i in re.finditer('src="(?P<Photo>.+)" ', self._read_file(i))])
        return sp


class Video(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_videos(self):
        res = []
        for i in self._get_paths_by_key('video-albums'):
            res.extend([i.groupdict() for i in re.finditer('<a href="(?P<Video>.*)">\n', self._read_file(i))])
        return res


class Profile(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_blacklist(self):
        mass = re.finditer(r"""href="(?P<Id>.+)" .*">(?P<Name>.+)</a></div>\n\s\s\n.*'>(?P<Date>.+)</div>""",
                           self._read_file('blacklist'))
        return self._date_corrector(mass)

    def get_documents(self):
        return [i.groupdict() for i in re.finditer('<a href="(?P<Document>.*)"', self._read_file('documents'))]

    def get_emails(self):
        return [i.groupdict() for i in re.finditer(r"main'>(?P<Email>\S+).*</div>", self._read_file('email-changes'))]

    def get_requests(self):
        return [i.groupdict() for i in
                re.finditer('href="(?P<Id>.+)">(?P<Name>.*)</a><', self._read_file('friends-requests'))]

    def get_friends(self):
        return [i.groupdict() for i in
                re.finditer('href="(?P<Id>.+)">(?P<Name>.*)</a><', self._read_file('friends0.html'))]

    def get_names(self):
        mass = re.finditer(
            r"""main'>(?P<Result>\w+).+имени (?P<Prev>\w+ \w+) на (?P<Next>\w+ \w+)</div>\s+.+>(?P<Date>.+)</div>""",
            self._read_file('name-changes'))
        return self._date_corrector(mass)

    def get_page_info(self):
        mass = re.finditer(
            r"""tertiary">(?P<Type>.+)(?:</div><div>|</div>\s{3}<div>(?:<a href="(?P<Id>.+) c.+ >)?)(?P<Value>.+)(?(Id)</a></div>|</div>)""",
            self._read_file('page-info'))
        return [i.groupdict() for i in mass]

    def get_phones(self):
        mass = re.finditer(r"main'>(?P<Result>\w+).+(?P<Number>\d{11}).+\n\s+.+'>(?P<Date>.+)</div>",
                           self._read_file('phone-changes'))
        return self._date_corrector(mass)

    def get_stories(self):
        return re.findall('href="(.+)">vk', self._read_file('stories'))

    def get_subs(self, filepath_or_name_or_all):
        if filepath_or_name_or_all.lower() != 'all':
            try:
                with open(filepath_or_name_or_all, encoding='utf-8') as file:
                    file = [i.strip().lower() for i in file.readlines()]
                    return [i.groupdict() for j in file for i in
                            re.finditer('href="(?P<Url>.+)">(?P<Name>.*)</a></div>',
                                        self._read_file('subscriptions0.html'))
                            if j in i.groupdict()['Name'].lower()]
            except FileNotFoundError:
                return [i.groupdict() for i in
                        re.finditer('href="(?P<Url>.+)">(?P<Name>.*)</a></div>', self._read_file('subscriptions0.html'))
                        if
                        filepath_or_name_or_all.lower() in i.groupdict()['Name'].lower()]
        return re.findall('href="(?P<Url>.+)">(?P<Name>.*)</a></div>', self._read_file('subscriptions0.html'))


class Wall(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_wall(self):
        res = []
        for i in self._get_paths_by_key('wall'):
            res.extend([i.groupdict() for i in
                        re.finditer('<a class="post__link fl_l" href="(?P<Url>.*)">', self._read_file(i))])
        return res


strt = time.perf_counter()
ax = Messages(r'D:\archive.zip', Users(r'D:\archive.zip').get_every()).get_top_words()
print(ax, time.perf_counter() - strt)
