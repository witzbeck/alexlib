from argparse import ArgumentParser

from __init__ import proj
from alexlib.constants import PROJECT_PATH
from alexlib.core import show_environ, show_dict, Version
from alexlib.files.objects import Directory


def main():
    parser = ArgumentParser(description="CLI for the alexlib package")
    parser.add_argument(
        'command',
        choices=['show_environ', 'show_project', '--version'],
        help="The command to run"
    )


    args = parser.parse_args()
    if args.command == 'show_environ':
        show_environ()
    elif args.command == 'show_project':
        d = Directory.from_path(PROJECT_PATH)
        show_dict(d.tree)
    elif args.command == '--version':
        v = Version.from_pyproject()
        print(v)




if __name__ == '__main__':
    main()