from .constants import LESSON_ID_LENGTH

class LessonCodeConverter:
    regex = rf"[A-Za-z0-9]{{{LESSON_ID_LENGTH}}}"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
