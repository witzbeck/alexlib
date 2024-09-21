from argparse import ArgumentParser

from alexlib.constants import PROJECT_PATH
from alexlib.core import show_environ
from alexlib.files.objects import Directory


def main():
    parser = ArgumentParser(description="CLI for the alexlib package")
    parser.add_argument(
        "--show",
        help="Displays the project tree or environment variables",
        choices=["environ", "project", "tree"],
    )

    args = parser.parse_args()
    if args.show == "environ":
        show_environ()
    elif args.show in ["project", "tree"]:
        Directory.from_path(PROJECT_PATH).show_tree()
    else:
        print(f"Invalid command = {args.command}")


if __name__ == "__main__":
    main()
