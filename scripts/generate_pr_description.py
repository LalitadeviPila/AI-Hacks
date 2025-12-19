
#!/usr/bin/env python3
"""
Generate a Pull Request description based on the DIFF between PR head and base.
Fall back to file-level summaries, commit messages, or a structured template
when line-level patches are unavailable.

Environment variables required:
- PR_TOKEN            : GitHub token (use GITHUB_TOKEN in GitHub Actions)
- OPENAI_API_KEY      : OpenAI API key
- GITHUB_REPOSITORY   : "<owner>/<repo>"
- PR_NUMBER           : Pull request number (integer)

Recommended models:
- Highest quality: "gpt-4.1"
- Fast/cheaper:    "gpt-4o-mini"
"""

import os
import re
import sys
from typing import List
from github import Github
from openai import OpenAI

# ---------------------------
# Env vars
# ---------------------------
GITHUB_TOKEN = os.environ.get("PR_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")
PR_NUMBER = os.environ.get("PR_NUMBER")

def exit(msg: str, code: int = 1):
    print(msg)
    sys.exit(code)

if not GITHUB_TOKEN:
    exit("Missing github token environment variable PR_TOKEN.")
if not OPENAI_API_KEY:
    exit("Missing OPENAI_API_KEY.")
if not REPO_NAME:
    exit("Missing GITHUB_REPOSITORY (expected '<owner>/<repo>').")
if not PR_NUMBER:
    exit("Missing PR_NUMBER.")

# ---------------------------
# Clients
# ---------------------------
gh = Github(GITHUB_TOKEN)
try:
    repo = gh.get_repo(REPO_NAME)
except Exception as e:
    exit(f"Failed to access repository '{REPO_NAME}': {e}")

try:
    pr = repo.get_pull(int(PR_NUMBER))
except Exception as e:
    exit(f"Failed to access PR #{PR_NUMBER}: {e}")

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------
# Helpers to build content
# ---------------------------
def build_unified_diff(files: List, max_chars: int = 20000) -> str:
    """
    Construct a unified-diff-like text from PR files.
    Includes per-file header and a summary line. Truncates for safety.
    """
    parts = []
    for f in files:
        # status: added/modified/removed/renamed, additions/deletions
        header = f"--- a/{f.filename}\n+++ b/{f.filename}\n"
        summary = f"# changes: status={f.status} additions={f.additions} deletions={f.deletions}\n"
        patch = f.patch or ""  # None for binary/very large changes
        parts.append(header + summary + patch + "\n")
    combined = "\n".join(parts).strip()
    if not combined:
        return ""
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n# [diff truncated]\n"
    return combined

def build_file_summaries(files: List) -> str:
    """
    Minimal file-level summaries when line-level patches are unavailable.
    Explicitly calls out newly added files.
    """
    if not files:
        return ""
    lines = []
    for f in files:
        status = (f.status or "").lower()
        tag = "NEW FILE" if status == "added" else status
        lines.append(
            f"- {f.filename} ({tag}; additions={f.additions}, deletions={f.deletions})"
        )
    return "\n".join(lines)

def extract_linked_issue_tokens(body: str) -> str:
    """
    Naive extraction of linked issues from PR body:
    - "#123" GitHub issue references
    - "ABC-123" common Jira keys
    """
    if not body:
        return "none"
    tokens = re.findall(r"(#\d+|[A-Z]{2,}-\d+)", body)
    return ", ".join(tokens) if tokens else "none"

# ---------------------------
# Gather PR context
# ---------------------------
pr_title = pr.title or ""
pr_branch = pr.head.ref
base_branch = pr.base.ref
labels = ", ".join([l.name for l in pr.get_labels()]) if pr.get_labels() else "none"
linked_issues_text = extract_linked_issue_tokens(pr.body)

# Files and patches
files = list(pr.get_files())
has_file_entries = len(files) > 0
diff_snippet = build_unified_diff(files) if has_file_entries else ""
file_summaries = build_file_summaries(files) if has_file_entries else ""

# Optional: compare base/head to detect true equality
compare = None
no_branch_diff = False
try:
    compare = repo.compare(pr.base.sha, pr.head.sha)
    no_branch_diff = (compare.ahead_by == 0 and compare.behind_by == 0 and len(getattr(compare, "files", [])) == 0)
except Exception:
    # Some repos/permissions may restrict compare; ignore failures
    no_branch_diff = False

# Commit messages (fallback)
commit_messages = "\n".join([c.commit.message for c in pr.get_commits()]).strip()

# ---------------------------
# Build the prompt (diff-first, with fallbacks)
# ---------------------------
if diff_snippet:
    prompt = f"""
You are an expert software engineer and technical writer.

Write a concise and informative pull request description based on the DIFF below.
Prioritize what changed and why. Use clear, scannable bullet points.

PR Context:
- Title: {pr_title}
- Branch: {pr_branch} → Base: {base_branch}
- Labels: {labels}
- Linked issues: {linked_issues_text}

Unified Diff (truncated if too long):
{diff_snippet}

Sections required:

* Purpose
* Changes
* Impact
* Testing
  - Include steps/commands
  - Mention where to add local testing screenshots

Rules:
- Base summary only on the diff and PR metadata above.
- If anything is unknown, state it explicitly.
- Keep bullets short; avoid long paragraphs.
"""
elif file_summaries:
    # Covers cases like binary/large changes or "new files" with no patch
    prompt = f"""
You are an expert software engineer and technical writer.

No line-level diff is available, but the PR includes these file changes:
{file_summaries}

PR Context:
- Title: {pr_title}
- Branch: {pr_branch} → Base: {base_branch}
- Labels: {labels}
- Linked issues: {linked_issues_text}

Write a concise PR description with:

* Purpose
* Changes (call out newly added files explicitly and their likely role)
* Impact (risk, performance, security, infra considerations)
* Testing (how to validate locally/CI; where to add screenshots)

Rules:
- Be specific to the files listed.
- Do not invent code details beyond what filenames/paths imply.
- Use short bullet points.
"""
elif commit_messages:
    # When GitHub shows no file entries but commits exist
    prompt = f"""
You are an expert software engineer and technical writer.

No file diffs were available for this PR. Use the commit messages below:
{commit_messages}

Produce a concise PR description with:

* Purpose
* Changes
* Impact
* Testing (steps; where to add local screenshots)

Rules:
- Stay faithful to commit messages; do not speculate beyond them.
- Use bullet points; avoid long paragraphs.
"""
else:
    # Truly no signals → insert a structured template immediately
    template = """\
**Purpose**
- _[Describe the problem this PR solves and why now.]_

**Changes**
- _[List key modules/files impacted and the nature of changes (additions/deletions/refactors).]_

**Impact**
- _[Risks, performance, security, infra implications; migrations/rollout notes.]_

**Testing**
- _[Steps to test locally/CI, commands, sample payloads; add screenshots as needed.]_"""
    try:
        existing = pr.body or ""
        divider = "\n\n---\n**AI Generated Description (template):**\n"
        pr.edit(body=existing + divider + template)
        print("No diffs or commits found. Added a structured template for the author to fill in.")
    except Exception as e:
        exit(f"Failed to update PR description: {e}")
    sys.exit(0)

# ---------------------------
# OpenAI call
# ---------------------------
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Use "gpt-4.1" for highest quality
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    ai_description = response.choices[0].message.content.strip()
except Exception as e:
    print(f"AI API call failed: {e}")
    ai_description = "AI description generation failed."

# ---------------------------
# Update PR body safely
# ---------------------------
try:
    existing = pr.body or ""
    divider_label = "diff-based" if diff_snippet else ("file-summary" if file_summaries else "commits")
    divider = f"\n\n---\n**AI Generated Description ({divider_label}):**\n"
    pr.edit(body=existing + divider + ai_description)
    print("Successfully updated PR description.")
except Exception as e:
