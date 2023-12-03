from __future__ import annotations

import os
import typer

from functools import wraps
from typing import Tuple

from kishu import __app_name__, __version__
from kishu.commands import (
    CheckoutResult, CommitResult, DetachResult, InitResult,
    InstrumentResult, InstrumentStatus, into_json, KishuCommand
)
from kishu.notebook_id import NotebookId


kishu_app = typer.Typer(add_completion=False)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


def print_clean_errors(fn):
    @wraps(fn)
    def fn_with_clean_errors(*args, **kwargs):
        if os.environ.get("KISHU_VERBOSE") == "true":
            return fn(*args, **kwargs)
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"Kishu internal error ({type(e).__name__}).")
    return fn_with_clean_errors


def print_reattachment_message(response: InstrumentResult):
    """
    Prints reattachment message, returns whether or not to print the actual response message
    """
    if response.value == InstrumentStatus.already_attached:
        return True
    if response.value in [InstrumentStatus.reattach_succeeded, InstrumentStatus.reattach_init_fail]:
        print("Notebook instrumentation was present but not initialized, so attempting to re-initialize it")
        print(response.message)
        return True
    if response.value == InstrumentStatus.no_kernel:
        print("Notebook kernel not found. Make sure Jupyter kernel is running for requested notebook")
        return False
    if response.value == InstrumentStatus.no_metadata:
        print(response.message)
        return False


def print_init_message(response: InitResult) -> None:
    nb_id = response.notebook_id
    if response.status != "ok":
        error = response.message.split(": ")[0]
        if error == "FileNotFoundError":
            print("Notebook kernel not found. Make sure Jupyter kernel is running for requested notebook")
        else:
            print(response.message)
    else:
        assert nb_id is not None
        output_str = (
            f"Successfully initialized notebook {nb_id.path()}."
            f" Notebook key: {nb_id.key()}."
            f" Kernel Id: {nb_id.kernel_id()}"
        )
        print(output_str)


def print_detach_message(response: DetachResult, notebook_path: str) -> None:
    if response.status != "ok":
        error = response.message.split(": ")[0]
        if error == "FileNotFoundError":
            print("Notebook kernel not found. Make sure Jupyter kernel is running for requested notebook")
        else:
            print(response.message)
    else:
        print(f"Successfully detached notebook {notebook_path}")


def print_checkout_message(response: CheckoutResult) -> None:
    if not print_reattachment_message(response.reattachment):
        return
    if response.message:
        print(response.message)


def print_commit_message(response: CommitResult) -> None:
    if not print_reattachment_message(response.reattachment):
        return
    if response.status == "ok":
        print(f"Successfully committed, id: {response.message}")
    else:
        print(response.message)


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
@print_clean_errors
def init(
    notebook_path: str = typer.Argument(
        ...,
        help="Path to the notebook to initialize Kishu on.",
        show_default=False
    ),
) -> None:
    """
    Initialize Kishu instrumentation in a notebook.
    """
    print_init_message(KishuCommand.init(notebook_path))


@kishu_app.command()
@print_clean_errors
def detach(
    notebook_path: str = typer.Argument(
        ...,
        help="Path to the notebook to detach Kishu from.",
        show_default=False
    ),
) -> None:
    """
    Detach Kishu instrumentation from notebook
    """
    print_detach_message(KishuCommand.detach(notebook_path), notebook_path)


@kishu_app.command()
def log(
    notebook_path_or_key: str = typer.Argument(
        ...,
        help="Path to the target notebook or Kishu notebook key.",
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
    notebook_key = NotebookId.parse_key_from_path_or_key(notebook_path_or_key)
    if log_all:
        print(into_json(KishuCommand.log_all(notebook_key)))
    else:
        print(into_json(KishuCommand.log(notebook_key, commit_id)))


@kishu_app.command()
def status(
    notebook_path_or_key: str = typer.Argument(
        ...,
        help="Path to the target notebook or Kishu notebook key.",
        show_default=False
    ),
    commit_id: str = typer.Argument(..., help="Commit ID to get status.", show_default=False),
) -> None:
    """
    Show a commit in detail.
    """
    notebook_key = NotebookId.parse_key_from_path_or_key(notebook_path_or_key)
    print(into_json(KishuCommand.status(notebook_key, commit_id)))


@kishu_app.command()
@print_clean_errors
def commit(
    notebook_path_or_key: str = typer.Argument(
        ...,
        help="Path to the target notebook or Kishu notebook key.",
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
    print_commit_message(KishuCommand.commit(notebook_path_or_key, message=message))


@kishu_app.command()
@print_clean_errors
def checkout(
    notebook_path_or_key: str = typer.Argument(
        ...,
        help="Path to the target notebook or Kishu notebook key.",
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
    print_checkout_message(KishuCommand.checkout(
        notebook_path_or_key,
        branch_or_commit_id,
        skip_notebook=skip_notebook,
    ))


@kishu_app.command()
def branch(
    notebook_path_or_key: str = typer.Argument(
        ...,
        help="Path to the target notebook or Kishu notebook key.",
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
    notebook_key = NotebookId.parse_key_from_path_or_key(notebook_path_or_key)
    if create_branch_name is not None:
        print(into_json(KishuCommand.branch(notebook_key, create_branch_name, commit_id)))
    if delete_branch_name is not None:
        print(into_json(KishuCommand.delete_branch(
            notebook_key, delete_branch_name)))
    if rename_branch != (None, None):
        old_name, new_name = rename_branch
        print(into_json(KishuCommand.rename_branch(
            notebook_key, old_name, new_name)))


@kishu_app.command()
def tag(
    notebook_path_or_key: str = typer.Argument(
        ...,
        help="Path to the target notebook or Kishu notebook key.",
        show_default=False
    ),
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
    notebook_key = NotebookId.parse_key_from_path_or_key(notebook_path_or_key)
    if list_tag:
        print(into_json(KishuCommand.list_tag(notebook_key)))
    if tag_name is not None:
        print(into_json(KishuCommand.tag(notebook_key, tag_name, commit_id, message)))
    if delete_tag_name is not None:
        print(into_json(KishuCommand.delete_tag(notebook_key, delete_tag_name)))


"""
Kishu Experimental Commands.
"""


kishu_experimental_app = typer.Typer(add_completion=False)


@kishu_experimental_app.command()
def fegraph(
    notebook_path_or_key: str = typer.Argument(
        ...,
        help="Path to the target notebook or Kishu notebook key.",
        show_default=False
    ),
) -> None:
    """
    Show the frontend commit graph.
    """
    notebook_key = NotebookId.parse_key_from_path_or_key(notebook_path_or_key)
    print(into_json(KishuCommand.fe_commit_graph(notebook_key)))


@kishu_experimental_app.command()
def fecommit(
    notebook_path_or_key: str = typer.Argument(
        ...,
        help="Path to the target notebook or Kishu notebook key.",
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
    notebook_key = NotebookId.parse_key_from_path_or_key(notebook_path_or_key)
    print(into_json(KishuCommand.fe_commit(notebook_key, commit_id, vardepth)))


if os.environ.get("KISHU_ENABLE_EXPERIMENTAL", "false").lower() in ('true', '1', 't'):
    kishu_app.add_typer(kishu_experimental_app, name="experimental")


def main() -> None:
    kishu_app(prog_name=__app_name__)


if __name__ == "__main__":
    main()
