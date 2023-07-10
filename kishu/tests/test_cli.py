import pytest

from kishu.cli import Command, KishuCLIArguments


class TestKishuCLIArguments:

    def test_no_arg(self):
        args = KishuCLIArguments.from_argv([])
        assert args.command == Command.help
        assert args.notebook_id is None
        assert args.commit_id is None

    def test_help(self):
        with pytest.raises(SystemExit):
            KishuCLIArguments.from_argv(["--help"])

        with pytest.raises(SystemExit):
            KishuCLIArguments.from_argv(["random", "args?", "--help", "--commit_id"])

        with pytest.raises(SystemExit):
            KishuCLIArguments.from_argv(["random", "args?", "-h", "--commit_id"])

    def test_log(self):
        args = KishuCLIArguments.from_argv(['log', '--notebook_id', '123', '--commit_id', '4567'])
        assert args.command == Command.log
        assert args.notebook_id == '123'
        assert args.commit_id == '4567'

    def test_log_all(self):
        args = KishuCLIArguments.from_argv(['log_all', '--notebook_id', '123', '--commit_id', '4567'])
        assert args.command == Command.log_all
        assert args.notebook_id == '123'
        assert args.commit_id == '4567'

    def test_status(self):
        args = KishuCLIArguments.from_argv(['status', '--notebook_id', '123', '--commit_id', '4567'])
        assert args.command == Command.status
        assert args.notebook_id == '123'
        assert args.commit_id == '4567'
