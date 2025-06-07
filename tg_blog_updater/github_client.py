"""Handles GitHub interactions."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

from github import Auth, Github, InputGitTreeElement

from .utils import get_env

if TYPE_CHECKING:
    from pathlib import Path

github = Github(
    auth=Auth.Token(
        get_env("GITHUB_TOKEN"),
    ),
)
repo = github.get_repo(get_env("GITHUB_REPO_NAME").lower())


def commit_post(files: list[tuple[Path, str | bytes]], commit_message: str) -> str:
    """Commit multiple files to the GitHub repository.

    Args:
        files: A list of tuples where each tuple contains: (file_path, file_content)
        commit_message: The commit message to use.

    Raises:
        TypeError: If the content is not bytes or str.

    Returns:
        The SHA of the new commit.

    """
    ref = repo.get_git_ref("heads/main")  # or your branch
    latest_commit = repo.get_git_commit(ref.object.sha)
    base_tree = latest_commit.tree

    elements: list[InputGitTreeElement] = []
    for path, content in files:
        if isinstance(content, bytes):  # For photos, videos, etc.
            blob = repo.create_git_blob(
                base64.b64encode(content).decode("utf-8"), "base64"
            )
        elif isinstance(content, str):  # For the post content
            blob = repo.create_git_blob(content, "utf-8")
        else:
            msg = "Content must be bytes or str. Got: %s", type(content)
            raise TypeError(msg)

        elements.append(
            InputGitTreeElement(
                path=str(path),
                mode="100644",
                type="blob",
                sha=blob.sha,
            )
        )

    new_tree = repo.create_git_tree(elements, base_tree)

    new_commit = repo.create_git_commit(commit_message, new_tree, [latest_commit])

    ref.edit(new_commit.sha)

    return new_commit.sha
