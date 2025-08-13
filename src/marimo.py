import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell
def _():

    import marimo as mo
    import sqlite_functions as sqf
    return mo, sqf


@app.cell
def _():
    import sqlalchemy

    DATABASE_URL = "sqlite:///data/database.db"
    engine = sqlalchemy.create_engine(DATABASE_URL)
    return (engine,)


@app.cell
def _(engine, mo):
    _df = mo.sql(
        """
        DELETE FROM questions where id=190
        """,
        engine=engine
    )
    return


@app.cell
def _(sqf):
    questions = sqf.load_topic("Stranger Things")
    return (questions,)


@app.cell
def _(questions):
    for item in questions:
        print(item)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
