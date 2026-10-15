# GitHub Auto Unfollow Bot

Every day, unfollows people you follow who don't follow you back.

## Setup (5 steps)

1. Create a new GitHub repo (private is fine), e.g. `github-unfollow-bot`.
2. Upload these files, keeping the folder structure:
   - `unfollow.py`
   - `whitelist.txt`
   - `.github/workflows/unfollow.yml`
3. Create a token: GitHub -> Settings -> Developer settings -> Personal access tokens -> Tokens (classic) -> Generate new token. Tick only the `user:follow` scope. Copy it.
4. In your repo: Settings -> Secrets and variables -> Actions -> New repository secret.
   Name: `GH_PAT`, Value: the token.
5. Test first: Actions tab -> "Auto unfollow non-followers" -> Run workflow -> keep `dry_run` = `true`. Read the log to see who would be unfollowed.

## Going live

When the dry run looks right: Settings -> Secrets and variables -> Actions -> Variables tab -> New repository variable.
Name: `LIVE`, Value: `true`.
From then on the daily schedule really unfollows (max 30 per run).

## Protect accounts

Add usernames to `whitelist.txt` (one per line) for people you want to keep following, e.g. creators you admire.
