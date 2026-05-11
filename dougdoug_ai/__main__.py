try:
    from .app import main
except ImportError:
    from dougdoug_ai.app import main


if __name__ == "__main__":
    main()
