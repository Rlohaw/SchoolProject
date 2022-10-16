from zipcontrol import *

while True:
    zip_path = input('Укажите абсолютный путь к архиву: ')
    a = ZipControl(zip_path)
    if a.category != Messages:
        res = a.normal()
    else:
        res = a.msg()
    print(res)
    w = r'(\w+)'
    with open(f"archive-{re.findall(rf'{w}.zip', zip_path)[0]}.txt", 'w', encoding='ANSI') as file:
        file.writelines('\n'.join(map(lambda x: ';'.join(x) if not isinstance(x, str) else x, res)))
