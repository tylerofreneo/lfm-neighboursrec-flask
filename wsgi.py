from main import main

if __name__ == "__main__":
    main = main()
    main.run()
else:
    gunicorn_app = main()