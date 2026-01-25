
#!/usr/bin/env python3
"""
AI PR Assistant: Generate code review and a PR description.
"""

import os
import re
import sys
from typing import List, Tuple

from github import Github
from openai import OpenAI

# ---------------------------
# Env & Config
# ---------------------------
def exit_now(msg: str, code: int = 1):
    print(msg)
    sys.exit(code)

GITHUB_TOKEN = os.environ.get("PR_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")
PR_NUMBER = os.environ.get("PR_NUMBER")

if not GITHUB_TOKEN:
    exit_now("Missing github token environment variable PR_TOKEN.")
if not OPENAI_API_KEY:
    exit_now("Missing OPENAI_API_KEY.")
if not REPO_NAME:
    exit_now("Missing GITHUB_REPOSITORY (expected '<owner>/<repo>').")
if not PR_NUMBER:
    exit_now("Missing PR_NUMBER.")

MODEL = os.environ.get("OAI_MODEL", "gpt-4o-mini")
MAX_DIFF_CHARS = int(os.environ.get("MAX_DIFF_CHARS", "20000"))
ENABLE_REVIEW = os.environ.get("ENABLE_REVIEW", "true").lower() == "true"
ENABLE_DESCRIPTION = os.environ.get("ENABLE_DESCRIPTION", "true").lower() == "true"

# Marker block in PR body to make updates idempotent
DESC_MARKER_BEGIN = "<!-- AI_PR_DESC_BEGIN -->"
DESC_MARKER_END = "<!-- AI_PR_DESC_END -->"


gh = Github(GITHUB_TOKEN)
try:
    repo = gh.get_repo(REPO_NAME)
    pr = repo.get_pull(int(PR_NUMBER))
except Exception as e:
    exit_now(f"Failed to access repository '{REPO_NAME}': {e}")

oai = OpenAI(api_key=OPENAI_API_KEY)


def build_unified_diff(files: List, max_chars: int) -> str:
    """Create a unified-diff-like string from PR files with a brief header per file."""
    parts = []
    for f in files:
        header = f"--- a/{f.filename}\n+++ b/{f.filename}\n"
        summary = f"# changes: status={f.status} additions={f.additions} deletions={f.deletions}\n"
        patch = f.patch or ""  # GitHub may omit large/binary patches
        parts.append(header + summary + patch + "\n")
    combined = "\n".join(parts).strip()
    if not combined:
        return ""
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n# [diff truncated]\n"
    return combined

def build_file_summaries(files: List) -> str:
    """Minimal per-file summary for when no line patches are available."""
    if not files:
        return ""
    lines = []
    for f in files:
        status = (f.status or "").lower()
        tag = "NEW FILE" if status == "added" else status
        lines.append(f"- {f.filename} ({tag}; additions={f.additions}, deletions={f.deletions})")
    return "\n".join(lines)

def extract_linked_issue_tokens(body: str) -> str:
    """Extract '#123' or 'ABC-123' tokens from PR body for context."""
    if not body:
        return "none"
    tokens = re.findall(r"(#\d+|[A-Z]{2,}-\d+)", body)
    return ", ".join(tokens) if tokens else "none"

def gather_pr_context(pr_obj) -> Tuple[str, str, str, str, str, str, str]:
    """Collect PR metadata and change signals."""
    pr_title = pr_obj.title or ""
    pr_branch = pr_obj.head.ref
    base_branch = pr_obj.base.ref
    labels = ", ".join([l.name for l in pr_obj.get_labels()]) if pr_obj.get_labels() else "none"
    linked_issues_text = extract_linked_issue_tokens(pr_obj.body)

    files = list(pr_obj.get_files())
    has_file_entries = len(files) > 0
    diff_snippet = build_unified_diff(files, MAX_DIFF_CHARS) if has_file_entries else ""
    file_summaries = build_file_summaries(files) if has_file_entries else ""
    commit_messages = "\n".join([c.commit.message for c in pr_obj.get_commits()]).strip()

    return pr_title, pr_branch, base_branch, labels, linked_issues_text, diff_snippet, file_summaries, commit_messages

def upsert_block(original: str, content: str, begin_marker: str, end_marker: str) -> str:
    """Insert or replace a marked block in the PR body."""
    if original is None:
        original = ""
    pattern = re.compile(
        re.escape(begin_marker) + r".*?" + re.escape(end_marker),
        flags=re.DOTALL,
    )
    block = f"{begin_marker}\n{content}\n{end_marker}"
    if pattern.search(original):
        return pattern.sub(block, original)
    # append with separator if body exists
    sep = "\n\n---\n\n" if original.strip() else ""
    return original + sep + block

def call_openai(prompt: str) -> str:
    """Call OpenAI Chat Completions API with consistent settings."""
    try:
        resp = oai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        print(f"OpenAI API call failed: {e}")
        return ""

# ---------------------------
# Prompts for both code review and description
# ---------------------------
def make_review_prompt(pr_title, pr_branch, base_branch, labels, linked, diff_snippet, file_summaries, commit_messages) -> str:
    if diff_snippet:
        return f"""
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
- Linked issues: {linked}

Unified Diff (may be truncated):
{diff_snippet}

Rules:
- Base your review ONLY on the diff.
- Be specific and actionable.
- Do not rewrite code unless needed to illustrate a fix.
""".strip()
    if file_summaries:
        return f"""
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
""".strip()
    if commit_messages:
        return f"""
You are a senior software engineer performing a code review.

No file diffs were available. Review based on commit messages:

{commit_messages}

Provide:
- Risks
- Missing tests
- Architecture concerns
- Any red flags
""".strip()
    return "No diff, file summaries, or commit messages available. Provide a concise, generic review checklist."

def make_description_prompt(pr_title, pr_branch, base_branch, labels, linked, diff_snippet, file_summaries, commit_messages) -> str:
    if diff_snippet:
        return f"""
You are an expert software engineer and technical writer.

Write a concise and informative pull request description based on the DIFF below.
Prioritize what changed and why. Use clear, scannable bullet points.

PR Context:
- Title: {pr_title}
- Branch: {pr_branch} → Base: {base_branch}
- Labels: {labels}
- Linked issues: {linked}

Unified Diff (truncated if too long):
{diff_snippet}

Sections required:
* Purpose
* Changes
* Impact
* Testing
  - Include steps/commands
  - Note where to add local testing screenshots

Rules:
- Base summary only on the diff and PR metadata above.
- If anything is unknown, state it explicitly.
- Keep bullets short; avoid long paragraphs.
""".strip()
    if file_summaries:
        return f"""
You are an expert software engineer and technical writer.

No line-level diff is available, but the PR includes these file changes:
{file_summaries}

PR Context:
- Title: {pr_title}
- Branch: {pr_branch} → Base: {base_branch}
- Labels: {labels}
- Linked issues: {linked}

Write a concise PR description with:
* Purpose
* Changes (call out newly added files explicitly and their likely role)
* Impact (risk, performance, security, infra considerations)
* Testing (how to validate locally/CI; where to add screenshots)

Rules:
- Be specific to the files listed.
- Do not invent code details beyond what filenames/paths imply.
- Use short bullet points.
""".strip()
    if commit_messages:
        return f"""
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
""".strip()
    return """\
**Purpose**
- _[Describe the problem this PR solves and why now.]_

**Changes**
- _[List key modules/files impacted and the nature of changes (additions/deletions/refactors).]_

**Impact**
- _[Risks, performance, security, infra implications; migrations/rollout notes.]_

**Testing**
- _[Steps to test locally/CI, commands, sample payloads; add screenshots as needed.]_"""


def main():
    pr_title, pr_branch, base_branch, labels, linked, diff_snippet, file_summaries, commit_messages = (
        gather_pr_context(pr)
    )

    if ENABLE_DESCRIPTION:
        desc_prompt = make_description_prompt(
            pr_title, pr_branch, base_branch, labels, linked,
            diff_snippet, file_summaries, commit_messages
        )
        ai_desc = call_openai(desc_prompt)
        if ai_desc:
            try:
                new_body = upsert_block(pr.body or "", ai_desc, DESC_MARKER_BEGIN, DESC_MARKER_END)
                pr.edit(body=new_body)
                print("Updated PR description (AI section).")
            except Exception as e:
                print(f"Failed to update PR description: {e}")
    if ENABLE_REVIEW:
        review_prompt = make_review_prompt(
            pr_title, pr_branch, base_branch, labels, linked,
            diff_snippet, file_summaries, commit_messages
        )
        ai_review = call_openai(review_prompt)
        if not ai_review:
            ai_review = "AI code review generation failed."

        try:
            pr.create_issue_comment(f"### AI Code Review\n\n{ai_review}")
            print("Posted AI code review as PR comment.")
        except Exception as e:
            print(f"Failed to post AI review comment: {e}")

if __name__ == "__main__":
    main()
