class Brain:
    thoughts = []
    processed = []

    def add_thought(self, thought):
        self.thoughts.append(thought)

    def forget_current_thought(self):
        try:
            self.processed.append(self.thoughts.pop())
        except IndexError:
            pass

    def get_current_thought(self):
        return self.thoughts[len(self.thoughts) - 1] if len(self.thoughts) > 0 else None

    def think(self):
        self.processed = []
        while True:
            thought = self.get_current_thought()
            if callable(thought):
                # think again if thought returns true
                if thought():
                    continue
            break
