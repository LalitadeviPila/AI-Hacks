
import os
from github import Github
from openai import OpenAI

# --- Environment variables ---
github_token = os.environ.get("PR_TOKEN")
openai_api_key = os.environ.get("OPENAI_API_KEY")
repo_name = os.environ.get("GITHUB_REPOSITORY")
pr_number = os.environ.get("PR_NUMBER")

if not github_token:
    print("Missing github token environment variables.")
    exit(1)
if not openai_api_key:
    print("Missing openai_api_key.")
    exit(1)
if not pr_number:
    print("Missing pr number.")
    exit(1)

# --- Clients ---
g = Github(github_token)
repo = g.get_repo(repo_name)
pr = repo.get_pull(int(pr_number))
client = OpenAI(api_key=openai_api_key)

# --- Build a unified diff payload from PR changes ---
# PyGithub's `get_files()` returns per-file patches (unified diff format).
files = list(pr.get_files())

def build_diff_snippet(files, max_chars=20000):
    """
    Construct a unified diff-style snippet across all changed files.
    Trim to max_chars to keep prompt size safe.
    """
    parts = []
    for f in files:
        # f.patch can be None on very large files or certain changes (binary/too big)
        # Use filename + summary even when patch is missing.
        header = f"--- a/{f.filename}\n+++ b/{f.filename}\n"
        summary = f"# changes: additions={f.additions} deletions={f.deletions} status={f.status}\n"
        patch = f.patch or ""
        block = header + summary + patch + "\n"
        parts.append(block)

    combined = "\n".join(parts)
    if len(combined) > max_chars:
        # Hard truncate from the end (keeps file headers); you can improve with chunking if needed
        combined = combined[:max_chars] + "\n# [diff truncated]\n"
    return combined

diff_snippet = build_diff_snippet(files)

# --- Additional context from PR metadata (optional but helpful) ---
pr_title = pr.title or ""
pr_branch = pr.head.ref
base_branch = pr.base.ref
labels = ", ".join([l.name for l in pr.get_labels()]) if pr.get_labels() else ""
linked_issues = []
# Attempt to pull linked issues via PR body keywords (fallback if you don't use GH linking):
if pr.body:
    # naive extraction for "#123", "JIRA-123", etc. (keep simple)
    import re
    linked_issues = re.findall(r"(#\d+|[A-Z]{2,}-\d+)", pr.body)
linked_issues_text = ", ".join(linked_issues)

# --- Prompt that uses DIFF, not commit messages ---
prompt = f"""
You are an expert software engineer and technical writer.

Write a concise and informative pull request description based on the DIFF below.
Prioritize what changed and why, not just the code lines. Use clear, scannable bullets.

PR Context:
- Title: {pr_title}
- Branch: {pr_branch} → Base: {base_branch}
- Labels: {labels or "none"}
- Linked issues: {linked_issues_text or "none"}

Unified Diff (truncated if too long):
{diff_snippet}

Please produce a description with the following sections:

* Purpose
  - What problem does this change solve? Why now?

* Changes
  - Summarize key code changes (modules, functions, endpoints, configs).
  - Highlight breaking changes, public API or schema changes if any.

* Impact
  - Risk areas, performance, security, infra implications (e.g., AWS, CI/CD, feature flags).
  - Migrations or rollout considerations.

* Testing
  - How to test locally and in CI.
  - Include steps, commands, or sample payloads.
  - Mention where developers can add local testing screenshots if needed.

Keep it short and precise. Use bullet points, avoid long paragraphs.
"""

# --- Call OpenAI (chat-completions for compatibility with your code) ---
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Prefer a modern lightweight model. Use "gpt-4.1" for highest quality.
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    ai_description = response.choices[0].message.content.strip()
except Exception as e:
    print(f"AI API call failed: {e}")
    ai_description = "AI description generation failed."

# --- Update PR body safely ---
try:
    existing = pr.body or ""
    divider = "\n\n---\n**AI Generated Description (diff-based):**\n"
    pr.edit(body=existing + divider + ai_description)
    print("Successfully updated PR description with AI content (diff-based).")
except Exception as e:
    print(f"Failed to update PR description: {e}")
``
