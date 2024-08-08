from functools import wraps
from botpy.message import GroupMessage
import logging

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Set the logging level to debug

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

            _log.debug(f"Processing message: {content_lower}")

            for command in self.commands:
                for prefix in ['', '/', '!']:
                    if content_lower == prefix + command:
                        _log.debug(f"Command matched: {prefix + command}")
                        kwargs["params"] = [] if self.split_command else ''
                        return await func(*args, **kwargs)

                    if content_lower.startswith(prefix + command + ' '):
                        params = content_lower[len(prefix + command):].strip()
                        _log.debug(f"Command matched with params: {prefix + command}, params: {params}")
                        kwargs["params"] = (
                            params.split() if self.split_command else params
                        )
                        return await func(*args, **kwargs)

            return False

        Command.command_handlers.append(decorated)
        return decorated
