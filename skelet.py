import collections
import datetime
import locale
import re
import time
import zipfile
from bs4 import BeautifulSoup
import pandas as pd

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


def time_counter(func):
    def wrapper(*args, **kwargs):
        strt = time.perf_counter()
        res = func(*args, **kwargs)
        print(time.perf_counter() - strt)
        return res

    return wrapper


class Zip:
    def __init__(self, name):
        self.__zip = zipfile.ZipFile(name)
        self._path = tuple((i.filename for i in self.__zip.infolist() if not i.is_dir()))
        self.__directory = name

    def __del__(self):
        self.__zip.close()

    def _get_text(self, key):
        soup = self._read_file(key)
        text_dict = {i.get_text(): i.get('href') for i in soup.find_all('a')}
        return text_dict

    def _read_file(self, key):
        try:
            with self.__zip.open(*(i for i in self._path if key in i)) as file:
                return BeautifulSoup(file.read(), 'lxml')
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
                ex['date'] = ex['date'].replace('мая', 'май')
            res.append(ex)
        return sorted(res, key=lambda x: datetime.datetime.strptime(x['date'], '%d %b %Y в %H:%M'))


class Coordinates(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_coordinates(self):
        soup = self._read_file('geo-points')
        a = soup.find(class_='item__main').find('a')
        mass = a.get_text('|;|', strip=True).split()[1::2]
        return [{'link': a.get('href'), 'latitude': mass[0], 'longitude': mass[1]}]


class Ads(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_ads_personal_interest(self):
        return list(filter(lambda x: x['type'] == 'Пользовательский интерес', self.get_ads()))

    def get_ads_system(self):
        return list(filter(lambda x: x['type'] == 'Системный сегмент', self.get_ads()))

    def get_ads_other(self):
        return list(filter(lambda x: x['type'] == 'Сторонний сегмент', self.get_ads()))

    def get_ads(self):
        soup = self._read_file('interests')
        res = ({'interest': i.find(class_='item__main').get_text(), 'type': i.find(class_='item__tertiary').text} for i
               in soup.find_all(class_='item'))
        return res


class Apps(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_apps(self):
        soup = self._read_file('apps')
        return ({'app': i.get_text()} for i in soup.find_all(class_='item__main'))


class Audios(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_audios(self):
        audios = []
        for nam in self._get_text('audio-albums.html').values():
            read = self._read_file(nam)
            if read:
                g = ({'name': n, 'artist': a} for a, n in
                     map(lambda x: x.get_text().split(' — '), read.find_all(class_='audio__title')))
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
                [likes.append({'type': key, 'url': i.get_text()}) for i in read.find_all('a') if
                 i.get_text().startswith('https')]
        return sorted(likes, key=lambda x: x['type'])


class Users(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_groups(self):
        res = list(filter(lambda x: x['msgid'].startswith('-'), self.get_every()))
        return res

    def get_persons(self):
        res = list(filter(lambda x: 3 < len(x['msgid']) < 10 and not x['msgid'].startswith('-'), self.get_every()))
        return res

    def get_chats(self):
        res = list(filter(lambda x: len(x['msgid']) == 10 and x['msgid'].startswith('2'), self.get_every()))
        return res

    def get_every(self):
        soup = self._read_file('index-messages.html')
        res = ({'name': k, 'msgid': re.search(r'\d+', v).group()} for k, v in
               self._get_text('index-messages.html').items() if re.findall(r'\d+', v))
        return res

    def get_one(self, person_name):
        res = list(filter(lambda x: x['name'] == person_name, self.get_every()))
        return res


class Messages(Zip):
    def __init__(self, name, _work_dict):
        super().__init__(name)
        self._work_dict = _work_dict

    def __iter__(self):
        for i in map(lambda x: x['msgid'], self._work_dict):
            num = 0
            while rf"messages/{i}/messages{num}.html" in self._path:
                bs = self._read_file(rf"messages/{i}/messages{num}.html")
                num += 50

                ww = ('Видеозапись', 'Файл', 'Фотография', 'Сообщение удалено', 'Стикер', 'Запись со стены', 'Ссылка',
                      '(ред.)', 'Запись на стене')

                text = map(lambda x: tuple(filter(lambda x: x not in ww, [
                    x.find(class_='message__header').find('a').get('href') if x.find(class_='message__header').find(
                        'a') else 0] + x.get_text('||;||', strip=True).split('||;||'))),
                           bs.find_all(class_='message'))

                yield from ({'id': msg[0], 'name': 'Вы' if not msg[0] else msg[1],
                             'date': msg[1].lstrip('Вы, ') if not msg[0] else msg[2],
                             'text': '\n'.join(msg[2:]) if not msg[0] else '\n'.join(msg[3:])} for msg in
                            filter(lambda x: len(x) >= 2 if x[0] == 0 else len(x) >= 3, text))

    def search_by_words(self, words_or_file):
        try:
            with open(words_or_file, encoding='utf-8') as file:
                file = [i.strip().lower() for i in file.readlines()]
                return [sp for sp in self for ww in file if ww.lower() == sp['text'].lower()]
        except FileNotFoundError:
            return [sp for sp in self if words_or_file.lower() in sp['text'].lower()]

    def get_top_words(self):
        return collections.Counter(i.group().lower() for j in self for i in re.finditer(r'\w+', j['text'])).most_common(100)

    def get_kd(self):
        m = 0
        nm = 0
        for i in self:
            if i['name'] == 'Вы':
                txt = i['text'].split('\n')[0]
                if not txt.startswith('https'):
                    m += len(re.findall(r'(\w+)', i['text'].split('\n')[0]))
            else:
                txt = i['text'].split('\n')[0]
                if not txt.startswith('https'):
                    nm += len(re.findall(r'(\w+)', i['text'].split('\n')[0]))
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
ax = Messages(r'Z:\const\archive.zip', Users(r'Z:\const\archive.zip').get_every()).get_kd()
print(ax, time.perf_counter() - strt)
