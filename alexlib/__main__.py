from argparse import ArgumentParser

from __init__ import proj
from alexlib.core import show_environ, show_dict
from alexlib.files.objects import Directory


def main():
    parser = ArgumentParser(description="CLI for the alexlib package")
    parser.add_argument(
        'command',
        choices=['show_environ', 'show_project', 'show_version'],
        help="The command to run"
    )


    args = parser.parse_args()
    if args.command == 'show_environ':
        print(proj.show_environ())




if __name__ == '__main__':
    main()