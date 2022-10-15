import datetime
import locale
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
a = datetime.datetime.strptime('22 фев 2021 в 19:33', '%d %b %Y в %H:%M')
print(a)