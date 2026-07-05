from pathlib import Path


MAIN = Path("main.py")


def main():
    print("Desktop Experience files installed.")
    print("")
    print("New GUI shell:")
    print("  src/hadocs/gui/desktop_app.py")
    print("")
    print("Documentation:")
    print("  docs/DESKTOP_EXPERIENCE.md")
    print("")
    print("This patch does not automatically replace your current GUI.")
    print("Wire it in after checking your existing main.py/app.py generator function.")


if __name__ == "__main__":
    main()
