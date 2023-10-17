from __future__ import annotations

import os
import typer

from typing import Tuple

from kishu import __app_name__, __version__
from kishu.commands import KishuCommand, into_json


kishu_app = typer.Typer(add_completion=False)


@kishu_app.command()
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
    print(into_json(KishuCommand.list(list_all=list_all)))


@kishu_app.command()
def log(
    notebook_id: str = typer.Argument(
        ...,
        help="Notebook ID to interact with.",
        show_default=False
    ),
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
    )
) -> None:
    """
    Show a history view of commit graph.
    """
    if log_all:
        print(into_json(KishuCommand.log_all(notebook_id)))
    else:
        print(into_json(KishuCommand.log(notebook_id, commit_id)))


@kishu_app.command()
def status(
    notebook_id: str = typer.Argument(
        ...,
        help="Notebook ID to interact with.",
        show_default=False
    ),
    commit_id: str = typer.Argument(..., help="Commit ID to get status.", show_default=False),
) -> None:
    """
    Show a commit in detail.
    """
    print(into_json(KishuCommand.status(notebook_id, commit_id)))


@kishu_app.command()
def commit(
    notebook_id: str = typer.Argument(
        ...,
        help="Notebook ID to interact with.",
        show_default=False
    ),
    message: str = typer.Option(
        None,
        "-m",
        "--message",
        help="Commit message.",
        show_default=False,
    ),
) -> None:
    """
    Checkout a notebook to a commit.
    """
    print(into_json(KishuCommand.commit(notebook_id, message=message)))


@kishu_app.command()
def checkout(
    notebook_id: str = typer.Argument(
        ...,
        help="Notebook ID to interact with.",
        show_default=False
    ),
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
    )
) -> None:
    """
    Checkout a notebook to a commit.
    """
    print(into_json(KishuCommand.checkout(
        notebook_id,
        branch_or_commit_id,
        skip_notebook=skip_notebook,
    )))


@kishu_app.command()
def branch(
    notebook_id: str = typer.Argument(
        ...,
        help="Notebook ID to interact with.",
        show_default=False
    ),
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
        "--delete_branch_name",
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
        print(into_json(KishuCommand.branch(notebook_id, create_branch_name, commit_id)))
    if delete_branch_name is not None:
        try:
            print(into_json(KishuCommand.delete_branch(
                notebook_id, delete_branch_name)))
        except Exception as error:
            typer.echo(f"Error: {str(error)}", err=True)
            raise typer.Exit()
    if rename_branch != (None, None):
        old_name, new_name = rename_branch
        try:
            print(into_json(KishuCommand.rename_branch(
                notebook_id, old_name, new_name)))
        except Exception as error:
            # Old_name does not exist and/or new_name already exists
            typer.echo(f"Error: {str(error)}", err=True)
            raise typer.Exit()


@kishu_app.command()
def tag(
    notebook_id: str = typer.Argument(
        ...,
        help="Notebook ID to interact with.",
        show_default=False
    ),
    tag_name: str = typer.Argument(
        ...,
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
) -> None:
    """
    Create or edit tags.
    """
    print(into_json(KishuCommand.tag(notebook_id, tag_name, commit_id, message)))


"""
Kishu Experimental Commands.
"""


kishu_experimental_app = typer.Typer(add_completion=False)


@kishu_experimental_app.command()
def fegraph(
    notebook_id: str = typer.Argument(
        ...,
        help="Notebook ID to interact with.",
        show_default=False
    ),
) -> None:
    """
    Show the frontend commit graph.
    """
    print(into_json(KishuCommand.fe_commit_graph(notebook_id)))


@kishu_experimental_app.command()
def fecommit(
    notebook_id: str = typer.Argument(
        ...,
        help="Notebook ID to interact with.",
        show_default=False
    ),
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
    print(into_json(KishuCommand.fe_commit(notebook_id, commit_id, vardepth)))


if os.environ.get("KISHU_ENABLE_EXPERIMENTAL", "false").lower() in ('true', '1', 't'):
    kishu_app.add_typer(kishu_experimental_app, name="experimental")


def main() -> None:
    kishu_app(prog_name=__app_name__)


if __name__ == "__main__":
    main()
