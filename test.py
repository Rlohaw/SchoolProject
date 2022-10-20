import inspect
def test(a, b, c):
    pass

print(inspect.getfullargspec(test).args)