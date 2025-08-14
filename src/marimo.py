import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell
def _():
    from trivia import TriviaGame
    return (TriviaGame,)


@app.cell
def _(TriviaGame):
    trivia = TriviaGame()
    return (trivia,)


@app.cell
def _(trivia):
    trivia.run_quiz("Stranger Things")
    return


if __name__ == "__main__":
    app.run()
