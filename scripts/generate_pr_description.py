import os
from github import Github
from openai import OpenAI

# Get environment variables
github_token = os.environ.get("GITHUB_TOKEN")
openai_api_key = os.environ.get("OPENAI_API_KEY")
repo_name = os.environ.get("GITHUB_REPOSITORY")
pr_number = os.environ.get("GITHUB_EVENT_PULL_REQUEST_NUMBER")

if not github_token or not openai_api_key or not pr_number:
    print("Missing required environment variables.")
    exit(1)

# Initialize GitHub and OpenAI clients
g = Github(github_token)
repo = g.get_repo(repo_name)
pr = repo.get_pull(int(pr_number))
client = OpenAI(api_key=openai_api_key)

# Extract info for the AI prompt (e.g., title, commit messages)
commit_messages = "\n".join([commit.commit.message for commit in pr.get_commits()])
# You could also fetch the diff if needed, but commit messages are a good start.

prompt = f"""
You are an expert software engineer and technical writer. 
Please write a concise and informative pull request description based on the following commit messages:
{commit_messages}

Ensure the description includes:
*   Purpose: The main goal of the changes.
*   Changes: A summary of modifications.
*   Impact: Any potential effects.
*   Testing: How to test the changes.
"""

# Generate description using the AI model
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", # Or another suitable model
        messages=[{"role": "user", "content": prompt}]
    )
    ai_description = response.choices[0].message.content.strip()
except Exception as e:
    print(f"AI API call failed: {e}")
    ai_description = "AI description generation failed."

# Update the PR description
try:
    pr.edit(body=pr.body + "\n\n---\n**AI Generated Description:**\n" + ai_description)
    print("Successfully updated PR description with AI content.")
except Exception as e:
    print(f"Failed to update PR description: {e}")
