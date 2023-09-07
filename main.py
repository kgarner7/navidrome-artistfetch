from argparse import ArgumentParser, Namespace
from collections.abc import Collection
from datetime import datetime, timezone
from getpass import getpass
from sys import stdout

from typing import Any, Dict, Iterator, List, Optional, Tuple, TypeVar

from dateutil.parser import parse
from requests import Session


def parse_args() -> "Namespace":
    parser = ArgumentParser(
        "Artist Fetch", description="Tool to query Navidrome and fetch artist images"
    )
    parser.add_argument(
        "server",
        type=str,
        help="The base url to your server (e.g. https://music.example.com)",
    )
    parser.add_argument(
        "-u",
        "--username",
        default=None,
        help="The username you want to authenticate as. If not provided, you will be prompted in console",
    )
    parser.add_argument(
        "-p",
        "--password",
        default=None,
        help="The password you want to authenticate as. If not provided, you will be prompted in console. Caution: If set, your password may be saved in your shell's history",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="If true, try and fetch artist images even if the last fetch time was recent",
    )
    parser.add_argument(
        "-d",
        "--days-since",
        default=7,
        type=int,
        help="How many days until external info is considered 'stale' and will be refetched",
    )

    return parser.parse_args()


def authenticate(
    session: "Session",
    server: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    retries=5,
) -> Tuple[Dict[str, str], str]:
    for _ in range(retries):
        if username is None:
            username = getpass("Username: ")

        if password is None:
            password = getpass("Password: ")

        response = session.post(
            f"{server}/auth/login", json={"username": username, "password": password}
        )

        if not response.ok:
            print("Could not authenticate: ", response.text)
            username = None
            password = None
        else:
            break

    if not username:
        print(f"Gave up after {retries} attempts.")
        exit(-1)

    data = response.json()
    navi_token = data["token"]

    subsonic_credentials = {
        "u": username,
        "t": data["subsonicToken"],
        "s": data["subsonicSalt"],
        "f": "json",
        "c": "Navidrome Artist Fetcher",
        "v": "1.8.0",
    }

    return (subsonic_credentials, navi_token)


T = TypeVar("T")


def progressbar(it: Collection[T], size=60, out=stdout) -> Iterator[T]:
    # Adapted from https://stackoverflow.com/questions/3160699
    count = len(it)

    def show(j):
        x = int(size * j / count)
        print(
            f"[{'#' * x}{'.' * (size - x)}] {j}/{count}",
            end="\r",
            file=out,
            flush=True,
        )

    show(0)
    for i, item in enumerate(it):
        yield item
        show(i + 1)

    print("\n", flush=True, file=out)


def do_fetch(
    session: "Session",
    server: str,
    subsonic: Dict[str, str],
    navidrome: str,
    force=False,
    old_days=7,
) -> None:
    artists = session.get(
        f"{server}/api/artist", headers={"x-nd-authorization": f"Bearer {navidrome}"}
    )

    if not artists.ok:
        print("Failed to fetch artists", artists.text)

    artist_data: List[Dict[str, Any]] = artists.json()
    print(f"Refreshing {len(artist_data)} artists")

    now = datetime.now(timezone.utc)

    total_changed = 0
    total_skipped = 0

    if len(artist_data) > 0:
        for artist in progressbar(artist_data):
            last_updated = artist.get(
                "externalInfoUpdatedAt", "0001-01-01T00:00:00+00:00"
            )

            try:
                navi_date = datetime.fromisoformat(last_updated)
            except:
                navi_date = parse(last_updated)

            if force or (now - navi_date).days >= old_days:
                artist_info = session.get(
                    f"{server}/rest/getArtistInfo",
                    params={**subsonic, "id": artist["id"]},
                )

                if not artist_info.ok:
                    print(
                        f"WARNING: Failed to fetch {artist['name']}: {artist_info.text}"
                    )

                artist_json = artist_info.json()

                new_update = artist_json.get("externalInfoUpdatedAt", last_updated)
                total_changed += new_update != last_updated
            else:
                total_skipped += 1

    print(
        f"Done! {total_skipped} skipped, {total_changed} updated, {len(artist_data) - total_changed - total_skipped} unchanged"
    )


if __name__ == "__main__":
    args = parse_args()

    session = Session()
    subsonic, navidrome = authenticate(
        session, args.server, args.username, args.password
    )
    do_fetch(session, args.server, subsonic, navidrome, args.force, args.days_since)
