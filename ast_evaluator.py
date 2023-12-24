from terminal import Terminal


class ExecutionFrame:
    def __init__(self, _locals, _globals, evaluator: 'AstEvaluator'):
        self.locals = _locals
        self.globals = _globals
        self._evaluator = evaluator

    def new_frame(self):
        return self._evaluator.new_frame()

    def close_frame(self):
        return self._evaluator.close_frame()

    def set_local(self, key, value):
        self.locals[key] = value


class AstEvaluator:
    def __init__(self):
        self.frame_stack: list[ExecutionFrame] = [ExecutionFrame({}, {}, self)]

    @property
    def frame(self):
        return self.frame_stack[-1]

    @property
    def global_frame(self):
        return self.frame_stack[0]

    def evaluate(self, ast: Terminal):
        value = ast.evaluate(self.frame)
        return value

    def new_frame(self):
        frame = ExecutionFrame(self.global_frame.globals, {}, self)
        self.frame_stack.append(frame)
        return frame

    def close_frame(self):
        if len(self.frame_stack) <= 1:
            raise IndexError("First(global) frame cannot be closed.")

        return self.frame_stack.pop()
