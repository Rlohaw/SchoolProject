import collections
import datetime
import locale
import re
import time
import zipfile
from bs4 import BeautifulSoup

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
        self._zip = zipfile.ZipFile(name)
        self._path = tuple((i.filename for i in self._zip.infolist() if not i.is_dir()))
        self._directory = name

    def __del__(self):
        self._zip.close()

    def _get_text(self, key):
        soup = self._read_file(key)
        text_dict = {i.get_text(): i.get('href') for i in soup.find_all('a')}
        return text_dict

    def _read_file(self, key):
        try:
            with self._zip.open(*(i for i in self._path if key in i)) as file:
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
        return [{'link': a.get('href'), 'latitude': mass[0].strip(','), 'longitude': mass[1]}]


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
        res = [{'interest': i.find(class_='item__main').get_text(), 'type': i.find(class_='item__tertiary').text} for i
               in soup.find_all(class_='item')]
        return res


class Apps(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_apps(self):
        soup = self._read_file('apps')
        return [{'app': i.get_text()} for i in soup.find_all(class_='item__main')]


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
        res = [{'name': k, 'msgid': re.search(r'[0-9-]+', v).group()} for k, v in
               self._get_text('index-messages.html').items() if re.findall(r'[0-9-]+', v)]
        return res

    def get_one(self, person_name):
        res = list(filter(lambda x: x['name'] == person_name, self.get_every()))
        return res


class Messages(Zip):
    def __init__(self, name, _work_dict):
        super().__init__(name)
        self._work_dict = _work_dict

    def __get_messages_iter(self):
        for i in map(lambda x: x['msgid'], self._work_dict):
            num = 0
            while rf"messages/{i}/messages{num}.html" in self._path:
                bs = self._read_file(rf"messages/{i}/messages{num}.html")
                num += 50

                ww = ('Видеозапись', 'Файл', 'Фотография', 'Сообщение удалено', 'Стикер', 'Запись со стены', 'Ссылка',
                      '(ред.)', 'Запись на стене', '1 прикреплённое сообщение')

                text = map(lambda x: tuple(filter(lambda x: x not in ww, [
                    x.find(class_='message__header').find('a').get('href') if x.find(class_='message__header').find(
                        'a') else 0] + x.get_text('||;||', strip=True).split('||;||'))),
                           bs.find_all(class_='message'))

                yield from ({'id': msg[0], 'name': 'Вы' if not msg[0] else msg[1],
                             'date': msg[1].lstrip('Вы, ') if not msg[0] else msg[2].lstrip(', '),
                             'text': '\n'.join(msg[2:]) if not msg[0] else '\n'.join(msg[3:])} for msg in
                            filter(lambda x: len(x) >= 2 if x[0] == 0 else len(x) >= 3, text))

    def get_all_messages(self):
        return [i for i in self.__get_messages_iter()]
    def get_text_messages(self):
        return [i.groupdict() for i in self]
    def __read_file_msg(self, key):
        try:
            with self._zip.open(*(i for i in self._path if key in i)) as file:
                return file.read().decode('ANSI')
        except TypeError:
            pass

    def __iter__(self):
        for i in map(lambda x: x['msgid'], self._work_dict):
            num = 0
            while rf"messages/{i}/messages{num}.html" in self._path:
                res = self.__read_file_msg(rf"messages/{i}/messages{num}.html")
                num += 50
                mass = re.finditer(
                    r"""header">(?:<a href="(?P<id>.+)">)?(?P<name>.+)(?(id)</a>, |, )(?P<date>[А-я0-9 :]+).*\n(?:(?:\s+.*\n){3| {2}<div>(?P<text>.+)<div class="kludges">)""",
                    res)
                yield from mass

    def search_by_words(self, words_or_file):
        try:
            with open(words_or_file, encoding='utf-8') as file:
                file = [i.strip().lower() for i in file.readlines()]
                return [sp.groupdict() for sp in self for ww in file if ww.lower() in sp['text'].lower()]
        except FileNotFoundError:
            mass = words_or_file.split()
            return [sp.groupdict() for sp in self for ww in mass if ww.lower() in sp['text'].lower()]

    def get_top_words(self):
        res = collections.Counter(
            w.group().lower() for msg in self for w in re.finditer(r'([A-zА-я]+)', msg['text'])).most_common()
        return [{'word': key, 'count': int(value)} for key, value in res]

    def get_kd(self):
        m = 0
        nm = 0
        for i in self:
            if i['name'] == 'Вы':
                m += len(re.findall(r'(\w+)', i['text']))
            else:
                nm += len(re.findall(r'(\w+)', i['text']))
        return [{'kd': round(m / nm, 2)}]

    def get_total_words(self):
        return [{'words': collections.Counter(
            w.group() for msg in self for w in re.finditer(r'([A-zА-я]+)', msg['text'])).total()}]


class Others(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_contacts(self):
        res = [{'number': j} for i in self._get_paths_by_key('other/external-contacts/archive') for j in
               map(lambda x: x.get_text(), self._read_file(i).find_all(class_='item__main'))]
        return res

    def get_bans(self):
        return [{'date': i} for i in
                map(lambda x: x.get_text(), self._read_file('bans.html').find_all(class_='item__tertiary'))]


class Payments(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_cards(self):
        return [{'number': i.get_text()} for i in self._read_file('cards-info').find_all(class_='item__main')]

    def get_payments_history(self):
        sp = self._read_file('payments-history')
        return [{'sum': i.find(class_='item__main').get_text(),
                 'operator': i.find(class_='item__main').find_next(class_='item__main').get_text(),
                 'date': i.find(class_='item__tertiary').get_text()} for i in sp.find_all(class_='item')]

    def get_votes(self):
        sp = self._read_file('/votes-history')
        return [{'trans': i.find(class_='item__main').get_text(),
                 'item': i.find(class_='item__main').find_next(class_='item__main').get_text(),
                 'date': i.find(class_='item__tertiary').get_text()} for i in sp.find_all(class_='item')]


class Photos(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_photos(self):
        return [{'url': j.get('src')} for i in self._get_paths_by_key('photos') for j in
                self._read_file(i).find_all('img')]


class Video(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_videos(self):
        return [{'video': j.find('a').get('href')} for i in self._get_paths_by_key('video-albums/') for j in
                self._read_file(i).find_all(class_='item__main') if j.find('a')]


class Profile(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_blacklist(self):
        return [{'id': i.find('a').get('href'),
                 'name': i.find('a').get_text(),
                 'date': i.find('div', class_='item__tertiary').get_text()}
                for i in self._read_file('blacklist').find_all(class_='item')]

    def get_documents(self):
        return [{'url': i.find('a').get('href'),
                 'name': i.find('a').get_text(),
                 'date': i.find('div', class_='item__tertiary').get_text()} for i in
                self._read_file('documents').find_all(class_='item')]

    def get_emails(self):
        return [{'mail': i.find(class_='item__main').get_text(),
                 'date': i.find(class_='item__tertiary').get_text()} for i in
                self._read_file('email-changes').find_all(class_='item')]

    def get_requests(self):
        return [{'id': j.find('a').get('href'),
                 'name': j.get_text(strip=True)} for i in self._get_paths_by_key('friends-requests') for j in
                self._read_file(i).find_all(class_='item')]

    def get_friends(self):
        return [{'id': j.find('a').get('href'),
                 'name': j.find(class_='item__main').get_text(),
                 'date': j.find(class_='item__tertiary').get_text()} for i in
                filter(lambda x: 'requests' not in x, self._get_paths_by_key('friends')) for j in
                self._read_file(i).find_all(class_='item')]

    def get_names(self):
        names = set()
        for i in self._read_file('name-changes').find_all(class_='item__main'):
            names.update(re.findall('[А-ЯA-Z]\w+ [А-ЯA-Z]\w+', i.get_text()))
        return [{'name': i} for i in names]

    def get_page_info(self):
        return [{'category': i.find(class_='item__tertiary').get_text(),
                 'answer': i.find('div').find_next('div').get_text().replace('\xa0', ' ') if i.find(
                     class_='item__tertiary').get_text() != 'Фотография' else i.find('img').get('src')} for i in
                self._read_file('page-info').find_all(class_='item')]

    def get_phones(self):
        return [{'operation': i.find(class_='item__main').get_text(),
                 'date': i.find(class_='item__tertiary').get_text()} for i in
                self._read_file('phone-changes').find_all(class_='item')]

    def get_stories(self):
        return [{'url': i.find('a').get('href'),
                 'date': i.find(class_='item__tertiary').get_text()} for i in
                self._read_file('stories').find_all(class_='item')]

    def get_subs(self, filepath_or_name_or_all):
        mass = [{'url': j.find('a').get('href'),
                 'name': j.get_text()} for i in self._get_paths_by_key('subscriptions') for j in
                self._read_file(i).find_all(class_='item__main')]
        if filepath_or_name_or_all.lower() != 'all':
            try:
                with open(filepath_or_name_or_all, encoding='utf-8') as file:
                    file = [i.strip().lower() for i in file.readlines()]
                    return [dct for dct in mass for rq in file if rq in dct['name'].lower()]
            except FileNotFoundError:
                return [dct for dct in mass if filepath_or_name_or_all.lower() in dct['name'].lower()]
        return mass


class Wall(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_wall(self):
        return [{'item': j.find(class_='attachment__description').get_text(),
                 'wall': j.find(class_='post__link fl_l').get('href')} for i in self._get_paths_by_key('wall') for j in
                self._read_file(i).find_all(class_='item') if j.find(class_='attachment__description')]
