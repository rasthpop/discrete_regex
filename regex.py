"""regex fsm"""

from __future__ import annotations
from abc import ABC, abstractmethod


class State(ABC):

    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def check_self(self, char: str) -> bool:
        """
        function checks whether occured character is handled by current ctate
        """
        pass

class StartState(State):
    next_states: list[State] = []

    def __init__(self):
        super().__init__()

    def check_self(self, char):
        return super().check_self(char)

    def __repr__(self):
        return "Start"
    
    def check_next(self, next_char: str) -> State | Exception:
        for state in self.next_states:
            if state.check_self(next_char):
                return state
        return TerminationState()



class TerminationState(State):
    def __init__(self):
        self.is_end = False
        self.next_states = [self]

    def check_self(self, char):
        return True
    def check_next(self, next_char: str) -> State | Exception:
        for state in self.next_states:
            if state.check_self(next_char):
                return state
        return TerminationState()



class DotState(State):
    """
    state for . character (any character accepted)
    """

    def __init__(self):
        self.is_end = False
        self.next_states = []

    def check_self(self, char: str):
        return True

    def check_next(self, next_char: str):
        for state in self.next_states:
            if state.check_self(next_char):
                return state

            if isinstance(state, StarState):
                return state.check_next(next_char)
        return TerminationState()
    
    def __repr__(self):
        return f"."

class AsciiState(State):
    """
    state for alphabet letters or numbers
    """

    def __init__(self, symbol: str) -> None:
        self.is_end = False
        self.next_states = []
        self.curr_sym = symbol

    def check_self(self, curr_char: str) -> State | Exception:
        if curr_char == self.curr_sym:
            print(f"Handled: {curr_char}")
            return True

        return False

    def check_next(self, next_char: str) -> State | Exception:
        for state in self.next_states:
            if isinstance(state, StarState):
                return state.check_next(next_char)

            if state.check_self(next_char):
                return state
        return TerminationState()

    def __repr__(self):
        return f"{self.curr_sym}"


class StarState(State):

    def __init__(self, checking_state: State, prev_state: State):
        self.is_end = False
        self.next_states = []
        self.checking_state = checking_state
        self.prev_state = prev_state

    def check_self(self, char):
        return self.checking_state.check_self(char)


    def check_next(self, next_char):
        if self.checking_state.check_self(next_char):
            return self

        for state in self.next_states:
            if isinstance(state, StarState):
                continue
            if state.check_next(next_char):
                return state
        return TerminationState()


    def __repr__(self):
        return f"{self.checking_state}*"

class PlusState(State):

    def __init__(self, checking_state: State):
        self.is_end = False
        self.next_states = []

        self.checking_state = checking_state
        self.loop_state = StarState(checking_state, checking_state)

        self.minimum_check = False

    def check_self(self, char):
        cur_check = self.checking_state if not self.minimum_check else self.loop_state

        if self.checking_state.check_self(char):
            self.minimum_check = True

        return cur_check.check_self and self.minimum_check

    def check_next(self, next_char):
        if self.checking_state.check_self(next_char):
            return self
        if self.minimum_check:
            for state in self.next_states:
                if isinstance(state, StarState):
                    return state.check_next(next_char)
                if state.check_next(next_char):
                    return state
        return TerminationState()


    def __repr__(self):
        return f"{self.checking_state}+"


class RegexFSM:
    curr_state: State = StartState()

    def __init__(self, regex_expr: str) -> None:
        prev_state = self.curr_state
        tmp_next_state = self.curr_state
        states = [self.curr_state]

        for i, char in enumerate(regex_expr):
            if char in '*+':
                continue

            tmp_next_state = self.__init_next_state(char, prev_state, tmp_next_state)

            if i + 1 < len(regex_expr) and regex_expr[i + 1] in '*+':
                tmp_next_state = self.__init_next_state(regex_expr[i + 1], prev_state, tmp_next_state)

            prev_state.next_states.append(tmp_next_state)
            if isinstance(prev_state, StarState):
                prev_state.prev_state.next_states.append(tmp_next_state)

            states.append(tmp_next_state)
            prev_state = tmp_next_state


        end_exists = False
        for state in reversed(states):
            if isinstance(state, StarState):
                state.is_end = True
            else:
                state.is_end = True
                end_exists = True
                break
        if not end_exists:
            states[-1].is_end = True

    def __init_next_state(
        self, next_token: str, prev_state: State, tmp_next_state: State
    ) -> State:
        new_state = None

        match next_token:
            case next_token if next_token == ".":
                new_state = DotState()
            case next_token if next_token == "*":
                new_state = StarState(tmp_next_state, prev_state)

            case next_token if next_token == "+":
                new_state = PlusState(tmp_next_state)

            case next_token if next_token.isascii():
                new_state = AsciiState(next_token)

            case _:
                raise AttributeError("Character is not supported")

        return new_state

    def check_string(self, reg_string: str):
        start_state_ref = self.curr_state

        for i, c in enumerate(reg_string):
            if isinstance(self.curr_state, (StarState, PlusState)) and isinstance(self.curr_state.checking_state, DotState):
                cur_next = self.curr_state.next_states[0]
                exit_phrase = cur_next.curr_sym
                while True:
                    for state in cur_next.next_states:
                        if isinstance(state, AsciiState):
                            exit_phrase += state.curr_sym
                            cur_next = state
                        if not cur_next.next_states:
                            break
                    if not cur_next.next_states:
                        break

                if reg_string[i: i + 1 + len(exit_phrase)] == exit_phrase:
                    self.curr_state = self.curr_state.next_states[0]

            else:
                self.curr_state = self.curr_state.check_next(c)

        result = self.curr_state.is_end
        self.curr_state = start_state_ref
        return result





if __name__ == "__main__":
    regex_pattern = "a*4.+hi"

    regex_compiled = RegexFSM(regex_pattern)

    print(regex_compiled.check_string("4uhi"))  # True
    print(regex_compiled.check_string("aaaaaa4uhi"))  # True
    print(regex_compiled.check_string("meow"))  # False
