#!/usr/bin/env python3
"""
Generate an AI-powered code review for a Pull Request based on the DIFF
between PR head and base. Falls back to file-level summaries or commit
messages when patches are unavailable.

Environment variables required:
- PR_TOKEN            : GitHub token (use GITHUB_TOKEN in GitHub Actions)
- OPENAI_API_KEY      : OpenAI API key
- GITHUB_REPOSITORY   : "<owner>/<repo>"
- PR_NUMBER           : Pull request number (integer)
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
# Helpers
# ---------------------------
def build_unified_diff(files: List, max_chars: int = 20000) -> str:
    parts = []
    for f in files:
        header = f"--- a/{f.filename}\n+++ b/{f.filename}\n"
        summary = f"# changes: status={f.status} additions={f.additions} deletions={f.deletions}\n"
        patch = f.patch or ""
        parts.append(header + summary + patch + "\n")
    combined = "\n".join(parts).strip()
    if not combined:
        return ""
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n# [diff truncated]\n"
    return combined

def build_file_summaries(files: List) -> str:
    if not files:
        return ""
    lines = []
    for f in files:
        status = (f.status or "").lower()
        tag = "NEW FILE" if status == "added" else status
        lines.append(f"- {f.filename} ({tag}; additions={f.additions}, deletions={f.deletions})")
    return "\n".join(lines)

def extract_linked_issue_tokens(body: str) -> str:
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

files = list(pr.get_files())
has_file_entries = len(files) > 0
diff_snippet = build_unified_diff(files) if has_file_entries else ""
file_summaries = build_file_summaries(files) if has_file_entries else ""

commit_messages = "\n".join([c.commit.message for c in pr.get_commits()]).strip()

# ---------------------------
# Build the AI prompt (code review)
# ---------------------------
if diff_snippet:
    prompt = f"""
You are a senior software engineer performing a code review.

Review the following DIFF and provide:

1. High-level feedback
2. Potential bugs or logical issues
3. Security concerns
4. Performance considerations
5. Code style / readability issues
6. Suggestions for improvement
7. Any missing tests or validation

PR Context:
- Title: {pr_title}
- Branch: {pr_branch} → Base: {base_branch}
- Labels: {labels}
- Linked issues: {linked_issues_text}

Unified Diff:
{diff_snippet}

Rules:
- Base your review ONLY on the diff.
- Be specific and actionable.
- Do not rewrite the code unless necessary to illustrate a fix.
"""
elif file_summaries:
    prompt = f"""
You are a senior software engineer performing a code review.

No line-level diff is available. Review the PR based on the file-level changes:

{file_summaries}

Provide:
- Potential risks
- Missing tests
- Architecture concerns
- Naming / structure issues
- Any red flags based on file roles

Do not invent code details beyond filenames.
"""
elif commit_messages:
    prompt = f"""
You are a senior software engineer performing a code review.

No file diffs were available. Review based on commit messages:

{commit_messages}

Provide:
- Risks
- Missing tests
- Architecture concerns
- Any red flags
"""
else:
    prompt = """
No diff, file summaries, or commit messages available.
Provide a generic checklist for the author to verify before merging.
"""

# ---------------------------
# OpenAI call
# ---------------------------
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    ai_review = response.choices[0].message.content.strip()
except Exception as e:
    print(f"AI API call failed: {e}")
    ai_review = "AI code review generation failed."

# ---------------------------
# Post review as PR comment
# ---------------------------
try:
    pr.create_issue_comment(f"### AI Code Review\n\n{ai_review}")
    print("Successfully posted AI code review as PR comment.")
except Exception as e:
    print(f"Failed to post PR comment: {e}")
