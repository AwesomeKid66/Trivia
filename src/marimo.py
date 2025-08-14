import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import sqlite_functions as sqf
    return (sqf,)


@app.cell
def _(sqf):
    sqf.delete_question(192)
    return


if __name__ == "__main__":
    app.run()
