import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import sqlite3 as sq
    import sqlite_functions as sqf
    return mo, sqf


@app.cell
def _():
    import sqlalchemy

    DATABASE_URL = "sqlite:///data/database.db"
    engine = sqlalchemy.create_engine(DATABASE_URL)
    return (engine,)


@app.cell
def _(sqf):
    sqf.add_question()
    return


@app.cell
def _(engine, mo):
    _df = mo.sql(
        f"""
        DELETE FROM questions where id=190
        """,
        engine=engine
    )
    return


if __name__ == "__main__":
    app.run()
