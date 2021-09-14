
 
class Col:
    def __init__(self, code, name):
        self.code = code
        self.name = name
        self.title = name

    def filter(self, product_qs):
        return product_qs
