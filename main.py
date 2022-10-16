from zipcontrol import *

choise = input('Хотите ли вы видеть результат в консоли?(y/n): ')
while True:
    zip_path = input('Укажите абсолютный путь к архиву: ')
    a = ZipControl(zip_path)
    if a.category != Messages:
        res = a.normal()
    else:
        res = a.msg()
    if choise == 'y':
        print(res)
    w = r'(\w+)'
    with open(f"archive-{re.findall(rf'{w}.zip', zip_path)[0]}.txt", 'w', encoding='ANSI') as file:
        if not isinstance(res, dict):
            file.writelines('\n'.join(map(lambda x: ', '.join(x) if not isinstance(x, str) else x, res)))
        else:
            fin = [f"{i}: {', '.join(res[i])}" for i in res]
            file.writelines('\n'.join(fin))
