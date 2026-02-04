
#!/usr/bin/env python3
import json
import os
import sys
import re
from typing import Optional
from github import Github
import subprocess

def eprint(*args):
    print(*args, file=sys.stderr)

def read_event():
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def has_trigger_phrase_in_push(event: dict, phrase: str) -> bool:
    if not phrase:
        return False
    pat = re.compile(re.escape(phrase), re.IGNORECASE)
    for c in event.get("commits", []):
        msg = c.get("message", "") or ""
        if pat.search(msg):
            return True
    return False

def first_subject_after_marker(event: dict, phrase: str) -> Optional[str]:
    if not phrase:
        return None
    pat = re.compile(re.escape(phrase), re.IGNORECASE)
    for c in event.get("commits", []):
        msg = (c.get("message", "") or "").strip()
        if pat.search(msg):
            first_line = msg.splitlines()[0]
            title = pat.sub("", first_line).strip(" :-–—")
            return title or None
    return None

def ensure_pr(repo, owner_login: str, head_branch: str, base_branch: str, title: str, body: str) -> int:
    # Dedup: if an open PR for this head already exists, reuse it
    open_prs = repo.get_pulls(state="open", head=f"{owner_login}:{head_branch}")
    for pr in open_prs:
        return pr.number

    pr = repo.create_pull(
        title=title or f"{head_branch} → {base_branch}",
        head=head_branch,
        base=base_branch,
        body=body or "Auto-created by AI PR Agent.",
        draft=False,
    )
    return pr.number

def call_ai_pr_assistant(pr_number: int):
    env = os.environ.copy()
    env["PR_NUMBER"] = str(pr_number)
    # Point to your existing script
    assistant_path = "scripts/ai_pr_assistant.py"
    if not os.path.exists(assistant_path):
        eprint(f"ERROR: {assistant_path} not found.")
        sys.exit(1)

    subprocess.run(
        [sys.executable, assistant_path],
        env=env,
        check=True,
    )


def main():
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    repo_full = os.environ.get("GITHUB_REPOSITORY")  # owner/repo
    head_branch = os.environ.get("GITHUB_REF_NAME")  # branch on push or PR head
    phrase = os.environ.get("PR_TRIGGER_PHRASE", "PR Create")
    base_branch_env = os.environ.get("BASE_BRANCH", "").strip()

    gh_token = os.environ.get("PR_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        eprint("Missing token: PR_TOKEN or GITHUB_TOKEN")
        sys.exit(1)

    gh = Github(gh_token)
    repo = gh.get_repo(repo_full)
    owner_login = repo.owner.login
    default_branch = repo.default_branch
    base_branch = base_branch_env or default_branch

    event = read_event()

    if event_name == "pull_request":
        pr_num = event.get("number") or event.get("pull_request", {}).get("number")
        if not pr_num:
            eprint("pull_request event without PR number?")
            sys.exit(0)
        print(f"[Agent] PR event detected → enrich PR #{pr_num}")
        call_ai_pr_assistant(int(pr_num))
        return

    if event_name == "push":
        # Ignore pushes to the base/default branch
        if head_branch in {base_branch, default_branch}:
            print(f"[Agent] Push to '{head_branch}' (base); skipping.")
            return

        if not has_trigger_phrase_in_push(event, phrase):
            print(f"[Agent] No commit with trigger phrase '{phrase}' found; skipping.")
            return

        title = first_subject_after_marker(event, phrase) or f"{head_branch} → {base_branch}"

        pr_body_placeholder = "<!-- AI_PR_DESC_BEGIN -->\n(Generating description…)\n<!-- AI_PR_DESC_END -->"
        pr_num = ensure_pr(repo, owner_login, head_branch, base_branch, title, pr_body_placeholder)
        print(f"[Agent] Using PR #{pr_num} for branch '{head_branch}'.")

        call_ai_pr_assistant(pr_num)
        return

    print(f"[Agent] Event '{event_name}' not handled; nothing to do.")

if __name__ == "__main__":
    main()
