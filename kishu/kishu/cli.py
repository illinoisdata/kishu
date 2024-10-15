from __future__ import annotations

from pathlib import Path
from typing import Tuple

import typer
from rich.console import Console

from kishu import __app_name__, __version__
from kishu.commands import KishuCommand
from kishu.storage.config import Config

kishu_app = typer.Typer(add_completion=False)
console = Console(soft_wrap=True)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@kishu_app.callback()
def app_main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show Kishu version.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    return


"""
Kishu Commands.
"""


@kishu_app.command()
def list(
    list_all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="List all Kishu sessions.",
    ),
) -> None:
    """
    List existing Kishu sessions.
    """
    console.print(KishuCommand.list(list_all=list_all))


@kishu_app.command()
def init(
    notebook_path: Path = typer.Argument(..., help="Path to the notebook to initialize Kishu on.", show_default=False),
) -> None:
    """
    Initialize Kishu instrumentation in a notebook.
    """
    console.print(KishuCommand.init(notebook_path))


@kishu_app.command()
def detach(
    notebook_path: Path = typer.Argument(..., help="Path to the notebook to detach Kishu from.", show_default=False),
) -> None:
    """
    Detach Kishu instrumentation from notebook
    """
    console.print(KishuCommand.detach(notebook_path))


@kishu_app.command()
def log(
    notebook_path: Path = typer.Argument(..., help="Path to the target notebook.", show_default=False),
    commit_id: str = typer.Argument(
        None,
        help="Show the history of a commit ID.",
        show_default=False,
    ),
    log_all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Log all commits.",
    ),
    graph: bool = typer.Option(
        False,
        "--graph",
        help="Display the commit graph.",
    ),
) -> None:
    """
    Show a history view of commit graph.
    """
    if log_all:
        console.print(KishuCommand.log_all(notebook_path))
    else:
        console.print(KishuCommand.log(notebook_path, commit_id))


@kishu_app.command()
def status(
    notebook_path: Path = typer.Argument(..., help="Path to the target notebook.", show_default=False),
    commit_id: str = typer.Argument(..., help="Commit ID to get status.", show_default=False),
) -> None:
    """
    Show a commit in detail.
    """
    console.print(KishuCommand.status(notebook_path, commit_id))


@kishu_app.command()
def commit(
    notebook_path: Path = typer.Argument(..., help="Path to the target notebook.", show_default=False),
    message: str = typer.Option(
        None,
        "-m",
        "--message",
        help="Commit message.",
        show_default=False,
    ),
    edit_branch_or_commit_id: str = typer.Option(
        None,
        "-e",
        "--edit-branch-name",
        "--edit_branch_name",
        "--edit-commit-id",
        "--edit_commit_id",
        help="Branch name or commit ID to edit.",
        show_default=False,
    ),
) -> None:
    """
    Create or edit a Kishu commit.
    """
    if edit_branch_or_commit_id:
        console.print(
            KishuCommand.edit_commit(
                notebook_path,
                edit_branch_or_commit_id,
                message=message,
            )
        )
    else:
        console.print(KishuCommand.commit(notebook_path, message=message))


@kishu_app.command()
def checkout(
    notebook_path: Path = typer.Argument(..., help="Path to the target notebook.", show_default=False),
    branch_or_commit_id: str = typer.Argument(
        ...,
        help="Branch name or commit ID to checkout.",
        show_default=False,
    ),
    skip_notebook: bool = typer.Option(
        False,
        "--skip-notebook",
        "--skip_notebook",
        help="Skip recovering notebook cells and outputs.",
    ),
) -> None:
    """
    Checkout a notebook to a commit.
    """
    console.print(
        KishuCommand.checkout(
            notebook_path,
            branch_or_commit_id,
            skip_notebook=skip_notebook,
        )
    )


@kishu_app.command()
def branch(
    notebook_path: Path = typer.Argument(..., help="Path to the target notebook.", show_default=False),
    commit_id: str = typer.Argument(
        None,
        help="Commit ID to create the branch on.",
        show_default=False,
    ),
    create_branch_name: str = typer.Option(
        None,
        "-c",
        "--create-branch-name",
        "--create_branch_name",
        help="Create branch with this name.",
        show_default=False,
    ),
    delete_branch_name: str = typer.Option(
        None,
        "-d",
        "--delete-branch-name",
        "--delete_branch_name",
        help="Delete branch with this name.",
        show_default=False,
    ),
    rename_branch: Tuple[str, str] = typer.Option(
        (None, None),
        "-m",
        "--rename-branch",
        "--rename_branch",
        help="Rename branch from old name to new name.",
        show_default=False,
    ),
) -> None:
    """
    Create, rename, or delete branches.
    """
    if create_branch_name is not None:
        console.print(KishuCommand.branch(notebook_path, create_branch_name, commit_id))
    if delete_branch_name is not None:
        console.print(KishuCommand.delete_branch(notebook_path, delete_branch_name))
    if rename_branch != (None, None):
        old_name, new_name = rename_branch
        console.print(KishuCommand.rename_branch(notebook_path, old_name, new_name))


@kishu_app.command()
def tag(
    notebook_path: Path = typer.Argument(..., help="Path to the target notebook.", show_default=False),
    tag_name: str = typer.Argument(
        None,
        help="Tag name.",
        show_default=False,
    ),
    commit_id: str = typer.Argument(
        None,
        help="Commit ID to create the tag on. If not given, use the current commit ID.",
        show_default=False,
    ),
    message: str = typer.Option(
        "",
        "-m",
        help="Message to annotate the tag with.",
    ),
    delete_tag_name: str = typer.Option(
        None,
        "-d",
        "--delete-tag-name",
        "--delete_tag_name",
        help="Delete tag with this name.",
        show_default=False,
    ),
    list_tag: bool = typer.Option(
        False,
        "-l",
        "--list",
        help="List tags.",
        show_default=False,
    ),
) -> None:
    """
    Create or edit tags.
    """
    if list_tag:
        console.print(KishuCommand.list_tag(notebook_path))
    if tag_name is not None:
        console.print(KishuCommand.tag(notebook_path, tag_name, commit_id, message))
    if delete_tag_name is not None:
        console.print(KishuCommand.delete_tag(notebook_path, delete_tag_name))


"""
Kishu Experimental Commands.
"""


kishu_experimental_app = typer.Typer(add_completion=False)


@kishu_experimental_app.command()
def fegraph(
    notebook_path: Path = typer.Argument(..., help="Path to the target notebook.", show_default=False),
) -> None:
    """
    Show the frontend commit graph.
    """
    console.print(KishuCommand.fe_commit_graph(notebook_path))


@kishu_experimental_app.command()
def fecommit(
    notebook_path: Path = typer.Argument(..., help="Path to the target notebook.", show_default=False),
    commit_id: str = typer.Argument(..., help="Commit ID to get detail.", show_default=False),
    vardepth: int = typer.Option(
        1,
        "--vardepth",
        help="Depth to resurce into variable attributes.",
    ),
) -> None:
    """
    Show the commit in frontend detail.
    """
    console.print(KishuCommand.fe_commit(notebook_path, commit_id, vardepth))


if Config.get("CLI", "KISHU_ENABLE_EXPERIMENTAL", False):
    kishu_app.add_typer(kishu_experimental_app, name="experimental")


def main() -> None:
    kishu_app(prog_name=__app_name__)


if __name__ == "__main__":
    main()
