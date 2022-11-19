class M:
    def __init__(self, amount) -> None:
        if isinstance(amount, self.__class__):
            self.value = amount.value
        else:
            self.value = int(amount * 1000)

    def dval(self):
        return self.value/1000

    def mval(self):
        return self.value

    def __add__(self, add):
        v = self.dval()
        if isinstance(add, self.__class__):
            add = add.dval()
        return M(v + add)

    def __int__(self):
        return int(self.value/1000)

    def __truediv__(self,other):
        return 