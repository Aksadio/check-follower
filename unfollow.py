"""
Unfollow everyone on GitHub who does not follow you back.

Environment variables:
  GH_TOKEN   Personal access token (classic) with the "user:follow" scope
  DRY_RUN    "true" (default) only prints who would be unfollowed
             set to "false" to really unfollow
  MAX_UNFOLLOWS  max unfollows per run (default 30)

Optional file: whitelist.txt (one username per line) - these accounts are
never unfollowed, even if they don't follow you back.
"""
import os
import random
import sys
import time

import requests

API = "https://api.github.com"
TOKEN = os.environ.get("GH_TOKEN")
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() != "false"
MAX_UNFOLLOWS = int(os.environ.get("MAX_UNFOLLOWS", "30"))

if not TOKEN:
    sys.exit("GH_TOKEN is missing. Add it as an environment variable / repo secret.")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def get_all(path):
    """Fetch every page of a list endpoint and return the usernames."""
    names, page = set(), 1
    while True:
        r = requests.get(
            f"{API}{path}",
            headers=HEADERS,
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        names.update(u["login"].lower() for u in data)
        page += 1
    return names


def load_whitelist():
    if not os.path.exists("whitelist.txt"):
        return set()
    with open("whitelist.txt", encoding="utf-8") as f:
        return {
            line.strip().lower()
            for line in f
            if line.strip() and not line.startswith("#")
        }


def main():
    followers = get_all("/user/followers")
    following = get_all("/user/following")
    whitelist = load_whitelist()
    print("Whitelist loaded:", sorted(whitelist))

    not_following_back = sorted(following - followers - whitelist)

    print(f"Followers: {len(followers)} | Following: {len(following)}")
    print(f"Not following you back: {len(not_following_back)}")
    print("Mode:", "DRY RUN (nothing will change)" if DRY_RUN else "LIVE")

    # Safety check: if followers came back empty, something is wrong. Stop.
    if not followers and following:
        sys.exit("Followers list is empty - aborting to be safe.")

    for user in not_following_back[:MAX_UNFOLLOWS]:
        if DRY_RUN:
            print(f"[dry-run] would unfollow {user}")
            continue
        r = requests.delete(f"{API}/user/following/{user}", headers=HEADERS, timeout=30)
        if r.status_code == 204:
            print(f"Unfollowed {user}")
        else:
            print(f"Failed to unfollow {user}: {r.status_code} {r.text}")
            if r.status_code in (403, 429):
                print("Rate limited - stopping this run.")
                break
        time.sleep(random.uniform(3, 8))  # be gentle with GitHub


if __name__ == "__main__":
    main()
