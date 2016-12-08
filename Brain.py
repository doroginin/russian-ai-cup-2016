from BrainState import BrainState
from Thought import Thought
from functools import reduce


class Brain:
    thoughts = []
    processed = []

    def add(self, what: Thought):
        if not isinstance(what, Thought):
            raise TypeError
        self.thoughts.append(what)
        return self

    def thought(self) -> Thought:
        return self.thoughts[len(self.thoughts) - 1] if len(self.thoughts) > 0 else None

    def think(self):
        while True:
            thought = self.thought()

            if thought is not None:
                state = _process_states(thought())
                self.processed.append(thought)

                if state & BrainState.done.value:
                    if callable(thought.done):
                        thought.done()
                    self.thoughts.remove(thought)
                if state & BrainState.think.value:
                    continue

            break

        return self

    def forget_processed_thoughts(self):
        self.processed = []

    def forget(self, name=None, n=1):
        if name is None and n != 0:
            try:
                self.thoughts.pop()
            except IndexError:
                pass
        else:
            for t in self.thoughts:
                if n == 0:
                    break
                if t.name == name:
                    self.thoughts.remove(t)
                    n -= 1
        return self


def _process_states(states):
    if states is None:
        return 0
    if isinstance(states, BrainState):
        return states.value
    if isinstance(states, tuple):
        return reduce(lambda x, y: x.value | y.value if isinstance(x, BrainState) and isinstance(y, BrainState) else 0,
                      states)
