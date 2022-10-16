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
        if isinstance(res, (list, tuple, set)):
            print('\n'.join(map(lambda x: ', '.join(map(str, x)) if not isinstance(x, str) else x, res)))
        elif isinstance(res, (int, float)):
            print(str(res))
        else:
            fin = [f"{i}: {', '.join(map(str, res[i])) if not isinstance(i, str) else res[i]}" for i in res]
            print('\n'.join(fin))
    w = r'(\w+)'
    with open(f"archive-{re.findall(rf'{w}.zip', zip_path)[0]}.txt", 'w', encoding='ANSI') as file:
        if isinstance(res, (list, tuple, set)):
            file.writelines('\n'.join(map(lambda x: ', '.join(map(str, x)) if not isinstance(x, str) else x, res)))
        elif isinstance(res, (int, float)):
            file.write(str(res))
        else:
            fin = [f"{i}: {', '.join(map(str, res[i])) if not isinstance(i, str) else res[i]}" for i in res]
            file.writelines('\n'.join(fin))
