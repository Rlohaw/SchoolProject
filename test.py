from datetime import datetime
import locale
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

text = '21 янв 2020 в 18:51:41'
res = datetime.strptime(text, '%d %b %Y в %H:%M:%S')
print(res)