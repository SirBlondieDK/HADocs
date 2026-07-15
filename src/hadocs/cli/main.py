import argparse
import sys

from src.hadocs.application import (
    DoctorApplication,
    GenerateApplication,
    InitApplication,
)


def main():
    parser = argparse.ArgumentParser(prog="hadocs", description="Home Assistant Documentation & Analysis")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("init", help="Create local configuration")
    sub.add_parser("doctor", help="Run safety and connection checks")
    sub.add_parser("generate", help="Generate documentation and analysis reports")
    sub.add_parser("gui", help="Open the graphical user interface")
    args = parser.parse_args()

    if args.command == "init":
        return cmd_init()
    if args.command == "doctor":
        return cmd_doctor()
    if args.command == "generate":
        return cmd_generate()
    if args.command == "gui":
        from src.hadocs.gui.app import run_gui
        run_gui()
        return 0

    parser.print_help()
    return 0


def cmd_init():
    return InitApplication().run()

def cmd_doctor():
    return DoctorApplication().run()

def cmd_generate():
    return GenerateApplication().run()


if __name__ == "__main__":
    sys.exit(main())
