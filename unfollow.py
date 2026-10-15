"""
GitHub follow-back + unfollow bot.

1. Follows back everyone who follows you (but you don't follow yet).
2. Unfollows everyone you follow who does not follow you back.

Environment variables:
  GH_TOKEN        Personal access token (classic) with the "user:follow" scope
  DRY_RUN         "true" (default) only prints what would happen
                  set to "false" to really follow / unfollow
  MAX_UNFOLLOWS   max unfollows per run (default 30)
  MAX_FOLLOWS     max follow-backs per run (default 30)

Optional files (one username per line, lines starting with # are ignored):
  whitelist.txt        never unfollowed, even if they don't follow you back
  no_followback.txt    never followed back, even if they follow you
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
MAX_FOLLOWS = int(os.environ.get("MAX_FOLLOWS", "30"))

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


def load_list(filename):
    if not os.path.exists(filename):
        return set()
    with open(filename, encoding="utf-8") as f:
        return {
            line.strip().lower()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        }


def pause():
    time.sleep(random.uniform(3, 8))  # be gentle with GitHub


def main():
    followers = get_all("/user/followers")
    following = get_all("/user/following")
    whitelist = load_list("whitelist.txt")
    no_followback = load_list("no_followback.txt")

    to_follow = sorted(followers - following - no_followback)
    to_unfollow = sorted(following - followers - whitelist)

    print(f"Followers: {len(followers)} | Following: {len(following)}")
    print("Whitelist loaded:", sorted(whitelist))
    print("No-followback list loaded:", sorted(no_followback))
    print(f"Follow back needed: {len(to_follow)}")
    print(f"Not following you back: {len(to_unfollow)}")
    print("Mode:", "DRY RUN (nothing will change)" if DRY_RUN else "LIVE")

    # Safety check: if followers came back empty, something is wrong. Stop.
    if not followers and following:
        sys.exit("Followers list is empty - aborting to be safe.")

    # Step 1: follow back new followers
    for user in to_follow[:MAX_FOLLOWS]:
        if DRY_RUN:
            print(f"[dry-run] would follow back {user}")
            continue
        r = requests.put(f"{API}/user/following/{user}", headers=HEADERS, timeout=30)
        if r.status_code == 204:
            print(f"Followed back {user}")
        else:
            print(f"Failed to follow {user}: {r.status_code} {r.text}")
            if r.status_code in (403, 429):
                print("Rate limited - stopping follow-backs this run.")
                break
        pause()

    # Step 2: unfollow people who don't follow back
    for user in to_unfollow[:MAX_UNFOLLOWS]:
        if DRY_RUN:
            print(f"[dry-run] would unfollow {user}")
            continue
        r = requests.delete(f"{API}/user/following/{user}", headers=HEADERS, timeout=30)
        if r.status_code == 204:
            print(f"Unfollowed {user}")
        else:
            print(f"Failed to unfollow {user}: {r.status_code} {r.text}")
            if r.status_code in (403, 429):
                print("Rate limited - stopping unfollows this run.")
                break
        pause()


if __name__ == "__main__":
    main()
