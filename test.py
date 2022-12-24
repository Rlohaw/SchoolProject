import collections
import datetime
import locale
import re
import zipfile

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


class Zip:
    def __init__(self, name):
        self.__zip = zipfile.ZipFile(name)
        self._path = tuple((i.filename for i in self.__zip.infolist() if not i.is_dir()))
        self.__directory = name

    def __del__(self):
        self.__zip.close()

    def _get_text(self, key):
        text = self._read_file(key)
        text_dict = dict(map(lambda x: reversed(x), re.findall('<a href="(.*)">(.*)</a>', text)))
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
        text = self._read_file('geo-points')
        coordinates = re.finditer("""<a href="(?P<Site>.+)">.+ (?P<Latitude>.+), (?P<Longitude>.+)</a></div>\n""", text)
        return [i.groupdict() for i in coordinates]


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
        text = self._read_file('interests')
        mass = re.finditer(r''''item__main'>(?P<Interest>.+)</div>\s+.+'item__tertiary'>(?P<Type>.+)</div>''', text)
        dct = [i.groupdict() for i in mass]
        return dct


class Apps(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_apps(self):
        mass = re.finditer("class='item__main'>(?P<App>.+)</div>", self._read_file('apps'))
        return sorted([i.groupdict() for i in mass], key=lambda x: x['App'])


class Audios(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_audios(self):
        audios = []
        for nam in self._get_text('audio-albums.html').values():
            if self._read_file(nam):
                text = self._read_file(nam)
                mass = re.finditer('audio__title">(?P<Name>.+) &mdash; (?P<Artist>.+)</div>', text)
                [audios.append(i.groupdict()) for i in mass if i.groupdict() not in audios]
        return sorted(audios, key=lambda x: x['Artist'])


class Likes(Zip):
    def __init__(self, name):
        super().__init__(name)

    def get_likes(self):
        likes = []
        for key, nam in self._get_text('likes.html').items():
            if self._read_file(nam):
                text = self._read_file(nam)
                mass = re.findall('<a href="(.*)">', text)
                [likes.append({'Type': key, 'Url': i}) for i in mass]
        return sorted(likes, key=lambda x: x['Type'])


class Users(Zip):
    def __init__(self, name):
        super().__init__(name)
        self.__messages = self._read_file('index-messages.html')

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
        res = re.finditer(r'<a href="(?P<MSGID>-?\d+).+>(?P<Name>.+)</a>\n', self.__messages)
        return [i.groupdict() for i in res]

    def get_one(self, person_name):
        return list(filter(lambda x: x['Name'] == person_name, self.get_every()))


class Messages(Zip):
    def __init__(self, name, _work_dict):
        super().__init__(name)
        self._work_dict = _work_dict

    def __iter__(self):
        for i in map(lambda x: x['MSGID'], self._work_dict):
            num = 0
            while rf"messages/{i}/messages{num}.html" in self._path:
                res = self._read_file(rf"messages/{i}/messages{num}.html")
                num += 50
                mass = re.finditer(
                    r"""header">(?:<a href="(?P<Id>.+)">)?(?P<Name>.+)(?(Id)</a>, |, )(?P<Date>[А-я0-9 :]+).*\n(?:(?:\s+.*\n){3}.*>(?P<Type>[А-я0-9]+).*\n.*href='(?P<Link>.*)'>| {2}<div>(?P<Text>.+)<div class="kludges">)""",
                    res)
                yield from mass

    def _file_messages(self):
        for msg in self:
            if msg.groupdict()['Link'] is not None:
                ex = msg.groupdict()
                if 'мая' in ex['Date']:
                    ex['Date'] = ex['Date'].replace('мая', 'май')
                    yield ex
                else:
                    yield ex

    def _text_messages(self):
        for msg in self:
            if msg.groupdict()['Text'] is not None:
                ex = msg.groupdict()
                ex['Text'] = ex['Text'].replace('<br>', '')
                if 'мая' in ex['Date']:
                    ex['Date'] = ex['Date'].replace('мая', 'май')
                    yield ex
                else:
                    yield ex

    def search_by_words(self, words_or_file):
        try:
            with open(words_or_file, encoding='utf-8') as file:
                file = [i.strip().lower() for i in file.readlines()]
                return sorted([sp for sp in self._text_messages() for ww in file if ww.lower() in sp['Text'].lower()],
                              key=lambda x: datetime.datetime.strptime(x['Date'], '%d %b %Y в %H:%M:%S'))
        except FileNotFoundError:
            mass = words_or_file.split()
            return sorted([sp for sp in self._text_messages() for ww in mass if ww.lower() in sp['Text'].lower()],
                          key=lambda x: datetime.datetime.strptime(x['Date'], '%d %b %Y в %H:%M:%S'))

    def get_top_words(self):
        res = collections.Counter(
            w.group() for msg in self._text_messages() for w in re.finditer(r'(\w+)', msg['Text']))
        return sorted([{'Word': key, 'Count': int(value)} for key, value in res.items()], key=lambda x: x['Count'],
                      reverse=True)

    def get_kd(self):
        m = 0
        nm = 0
        for i in self._text_messages():
            if i['Name'] == 'Вы':
                m += len(re.findall(r'(\w+)', i['Text']))
            else:
                nm += len(re.findall(r'(\w+)', i['Text']))
        return [{'Kd': round(m / nm, 2)}]

    def get_total_words(self):
        return [{'Words': collections.Counter(
            w.group() for msg in self._text_messages() for w in re.finditer(r'(\w+)', msg['Text'])).total()}]

    def get_messages(self):
        return sorted([i for i in self._text_messages()] + [i for i in self._file_messages()],
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
