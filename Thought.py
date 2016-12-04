class Thought:
    do = name = args = done = None

    def __init__(self, do: callable, name: str = None, args: (list, tuple) = None, done: callable = None):
        self.do = do
        if name is None:
            name = do.__name__
        self.name = name
        if args is None:
            args = []
        self.args = args
        self.done = done

    def __call__(self):
        return self.do()
