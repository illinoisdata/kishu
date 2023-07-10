from __future__ import annotations
import enum
import json
import simple_parsing
import dataclasses
from typing import Any, Callable, Dict, List, Optional

from kishu.commands import KishuCommand


"""
Printing dataclasses
"""


class DataclassJSONEncoder(json.JSONEncoder):

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        try:
            return super().default(o)
        except TypeError:
            return o.__repr__()


def print_dataclass(data: Any):
    print(json.dumps(data, cls=DataclassJSONEncoder, indent=2))


"""
Command Line Interface.
"""


class Command(enum.Enum):
    help = "help"
    log = "log"
    log_all = "log_all"
    status = "status"


@dataclasses.dataclass
class KishuCLIArguments:
    """Interact with Kishu-powered programs."""
    command: Command = Command.help  # Kishu command.
    notebook_id: Optional[str] = None  # Notebook ID to interact with.
    commit_id: Optional[str] = None  # Commit ID to apply command on.

    @staticmethod
    def from_argv(argv: List[str]) -> KishuCLIArguments:
        if (
            len(argv) >= 1
            and "--command" not in argv
            and "--help" not in argv
            and "-h" not in argv
        ):
            # Takes first argument as the command.
            argv = ["--command"] + argv
        return simple_parsing.parse(KishuCLIArguments, args=argv)

    @staticmethod
    def print_help() -> None:
        simple_parsing.parse(KishuCLIArguments, args="--help")


class KishuCLI:

    def __init__(self) -> None:
        # Per-session state goes here.
        self._commands: Dict[Command, Callable[[KishuCLIArguments], None]] = {
            Command.help: self.help,
            Command.log: self.log,
            Command.log_all: self.log_all,
            Command.status: self.status,
        }

    def exec(self, args):
        func = self.dispatch(args.command)
        func(args)

    def dispatch(self, command) -> Callable[[KishuCLIArguments], None]:
        return self._commands[command]

    def help(self, args):
        print(f"commands: {' | '.join([cmd.value for cmd in Command])}")
        KishuCLIArguments.print_help()

    def log(self, args):
        assert args.notebook_id is not None, "log requires notebook_id."
        assert args.commit_id is not None, "log requires commit_id."
        print_dataclass(KishuCommand.log(args.notebook_id, args.commit_id))

    def log_all(self, args):
        assert args.notebook_id is not None, "log_all requires notebook_id."
        print_dataclass(KishuCommand.log_all(args.notebook_id))

    def status(self, args):
        assert args.notebook_id is not None, "status requires notebook_id."
        assert args.commit_id is not None, "status requires commit_id."
        print_dataclass(KishuCommand.status(args.notebook_id, args.commit_id))


if __name__ == "__main__":
    # Parse argugments from command line.
    import sys
    args = KishuCLIArguments.from_argv(sys.argv[1:])

    # Execute
    cli = KishuCLI()
    cli.exec(args)
