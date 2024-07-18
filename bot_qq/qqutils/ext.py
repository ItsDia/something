from functools import wraps

from botpy.message import GroupMessage
from pydantic import BaseModel


class Command:
    command_handlers = []

    def __init__(self, *args, split_command=True):
        self.commands = args
        self.split_command = split_command

    def __call__(self, func):
        @wraps(func)
        async def decorated(*args, **kwargs):
            message: GroupMessage = kwargs["message"]
            content_lower = message.content.strip().lower()

            for command in self.commands:
                for prefix in ['', '/', '!']:
                    if content_lower == prefix + command:
                        kwargs["params"] = [] if self.split_command else ''
                        return await func(*args, **kwargs)

                    if content_lower.startswith(prefix + command + ' '):
                        params = content_lower[len(prefix + command):].strip()
                        kwargs["params"] = (
                            params.split() if self.split_command else params
                        )
                        return await func(*args, **kwargs)

            return False

        Command.command_handlers.append(decorated)
        return decorated

class UserProfileModel(BaseModel):
    headLogoURL: str
    username: str
    solved: int
    rating: int

    @property
    def level(self):
        rating_levels = {
            "newbie": range(0, 1200),
            "pupil": range(1200, 1400),
            "specialist": range(1400, 1600),
            "expert": range(1600, 1900),
            "candidate-master": range(1900, 2100),
            "master": range(2100, 2300),
            "international-master": range(2300, 2400),
            "grandmaster": range(2400, 2600),
            "international-grandmaster": range(2600, 3000),
            "legendary-grandmaster": range(3000, 9999),
        }
        for level, rating_range in rating_levels.items():
            if self.rating in rating_range:
                return level

    def serialize(self):
        model_dict = self.model_dump()
        model_dict["level"] = self.level
        return model_dict