import collections
import re
import zipfile


class Zip:
    __exemplar = None
    __slots__ = ('__zip', 'path')

    def __new__(cls, *args, **kwargs):
        if cls.__exemplar is None:
            cls.__exemplar = super().__new__(cls)
        return cls.__exemplar

    def __init__(self, name):
        self.__zip = zipfile.ZipFile(name)
        self.path = tuple((i.filename for i in self.__zip.infolist() if not i.is_dir()))

    def __del__(self):
        self.__zip.close()

    def __get_text(self, key):
        text = self.__read_file(key)
        text_dict = dict(map(lambda x: reversed(x), re.findall('<a href="(.*)">(.*)</a>', text)))
        return text_dict

    def __read_file(self, key):
        try:
            with self.__zip.open(*(i for i in self.path if key in i)) as file:
                return file.read().decode('ANSI')
        except TypeError:
            pass

    def coordinates(self):
        text = self.__read_file('geo-points')
        geo = re.search('<a href="(?P<site>.+)">(?P<lat>.+), (?P<lon>.+)</a>', text)
        return f"Геопозиция на картах:{geo['site']}\n{geo['lat']}\n{geo['lon']}"

    def ads(self):
        text = self.__read_file('interests')
        mass = re.findall('''item__main'>([А-яA-z0-9/ -–—,.()]+)</div>|item__tertiary'>([А-я ]+)</div>''', text)
        mass = list(map(lambda x: ''.join(x), mass))
        d = collections.defaultdict(list)
        [d[mass[i + 1]].append(mass[i]) for i in range(0, len(mass), 2)]
        return d

    def apps(self):
        text = re.findall("class='item__main'>([A-zА-я -]+)</div>", self.__read_file('apps'))
        return text

    def audios(self):
        d = collections.defaultdict(set)
        for nam in self.__get_text('audio-albums.html').values():
            if self.__read_file(nam):
                text = self.__read_file(nam)
                mass = re.findall('audio__title">(?P<name>.+) &mdash; (?P<artist>.+)</div>', text)
                [d[i[0]].update([i[1]]) for i in mass]
        return d

    def bookmarks(self):
        d = collections.defaultdict(list)
        for key, nam in self.__get_text('bookmarks.html').items():
            if self.__read_file(nam):
                text = self.__read_file(nam)
                mass = re.findall('<a href="(.*)">', text)
                d[key].extend(mass)
        return d

    def likes(self):
        d = collections.defaultdict(list)
        for key, nam in self.__get_text('likes.html').items():
            if self.__read_file(nam):
                text = self.__read_file(nam)
                mass = re.findall('<a href="(.*)">', text)
                d[key].extend(mass)
        return d


############################################
test = Zip(r'D:\sec\archive.zip')
print(test.likes())
