class Thought:
    do = name = args = None

    def __init__(self, boo: callable, name: str = None, args: (list, tuple) = None):
        self.do = boo
        if name is None:
            name = boo.__name__
        self.name = name
        if args is None:
            args = []
        self.args = args

    def __call__(self):
        return self.do()
