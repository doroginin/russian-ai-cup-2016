class Brain:
    thoughts = []
    processed = []

    def add_thought(self, thought):
        self.thoughts.append(thought)
        return self

    def forget_current_thought(self):
        try:
            self.thoughts.pop()
        except IndexError:
            pass
        return self

    def get_current_thought(self):
        return self.thoughts[len(self.thoughts) - 1] if len(self.thoughts) > 0 else None

    def think(self):
        while True:
            thought = self.get_current_thought()
            if callable(thought):
                self.processed.append(thought)
                # think again if thought returns true
                if thought():
                    continue
            else:
                self.forget_current_thought()
            break
        return self

    def forget_processed_thoughts(self):
        self.processed = []
