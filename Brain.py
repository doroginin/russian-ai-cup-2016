from BrainState import BrainState
from Thought import Thought
from functools import reduce


class Brain:
    thoughts = []
    processed = []

    def add(self, thought: Thought):
        if not isinstance(thought, Thought):
            raise TypeError
        self.thoughts.append(thought)
        return self

    def current(self) -> Thought:
        return self.thoughts[len(self.thoughts) - 1] if len(self.thoughts) > 0 else None

    def think(self):
        while True:
            thought = self.current()

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

    def forget(self, name=None):
        if name is None:
            try:
                self.thoughts.pop()
            except IndexError:
                pass
        else:
            for t in self.thoughts:
                if t.name == name:
                    self.thoughts.remove(t)
        return self


def _process_states(states):
    if states is None:
        return 0
    if isinstance(states, BrainState):
        return states.value
    if isinstance(states, tuple):
        return reduce(lambda x, y: x.value | y.value if isinstance(x, BrainState) and isinstance(y, BrainState) else 0,
                      states)
