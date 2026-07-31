import argparse
import json
import sys

from hadocs.application import (
    DoctorApplication,
    GenerateApplication,
    InitApplication,
)
from hadocs.version import __version__


def main():
    parser = argparse.ArgumentParser(prog="hadocs", description="Home Assistant Documentation & Analysis")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("init", help="Create local configuration")
    sub.add_parser("doctor", help="Run safety and connection checks")
    sub.add_parser("generate", help="Generate documentation and analysis reports")
    sub.add_parser("gui", help="Open the graphical user interface")
    sub.add_parser("hask-preview", help="Display redacted HASK Preview status")
    database = sub.add_parser("database", help="Manage the operational database")
    database_sub = database.add_subparsers(dest="database_command")
    database_sub.add_parser(
        "init", help="Explicitly initialize operational database identity"
    )
    database_sub.add_parser(
        "status", help="Display redacted operational database status"
    )
    args = parser.parse_args()

    if args.command == "init":
        return cmd_init()
    if args.command == "doctor":
        return cmd_doctor()
    if args.command == "generate":
        return cmd_generate()
    if args.command == "gui":
        from hadocs.gui.app import run_gui
        run_gui()
        return 0
    if args.command == "hask-preview":
        return cmd_hask_preview()
    if args.command == "database" and args.database_command == "init":
        return cmd_database_init()
    if args.command == "database" and args.database_command == "status":
        return cmd_database_status()

    parser.print_help()
    return 0


def cmd_init():
    return InitApplication().run()

def cmd_doctor():
    return DoctorApplication().run()

def cmd_generate():
    return GenerateApplication().run()


def cmd_hask_preview(*, config_loader=None):
    from hadocs.application.hask_preview import HaskPreviewService
    from hadocs.utils.config import load_config

    snapshot = HaskPreviewService().snapshot((config_loader or load_config)())
    print(json.dumps(snapshot.as_dict(), ensure_ascii=True, sort_keys=True))
    return 0


def cmd_database_init(*, config_loader=None, config_saver=None, secret_provider=None):
    from hadocs.application.database_status import initialize_database_identity
    from hadocs.application.operational_database import DatabaseIdentityInitializationState
    from hadocs.utils.config import load_config, save_database_identity_config

    load = config_loader or load_config
    save = config_saver or save_database_identity_config
    try:
        result, _ = initialize_database_identity(
            load(),
            secret_provider=secret_provider,
            save=save,
        )
    except (RuntimeError, TypeError, ValueError) as error:
        print(f"Database identity initialization failed: {error}")
        return 2

    if result.state is DatabaseIdentityInitializationState.ALREADY_INITIALIZED:
        print("Operational database identity is already initialized; no changes made.")
    else:
        print("Operational database identity initialized successfully.")
    return 0


def cmd_database_status(*, config_loader=None, secret_provider=None):
    from hadocs.application.database_status import read_operational_database_status
    from hadocs.utils.config import load_config

    load = config_loader or load_config
    try:
        status = read_operational_database_status(
            load(), secret_provider=secret_provider
        )
    except Exception:
        print("Operational database status is unavailable.")
        return 2
    for line in status.lines():
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
