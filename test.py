mass = ['6 мая 2022 в 0:27']
mass = [i if 'мая' not in i else i.replace('мая', 'май') for i in mass]
print(mass)