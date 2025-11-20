import uvicorn

from src import App
from src.dependencies.db import init_db

app = App()


def main():
    init_db()

    uvicorn.run(
        "main:app.api", host="0.0.0.0", port=5000, reload=True, reload_dirs=["src"]
    )


if __name__ == "__main__":
    main()
