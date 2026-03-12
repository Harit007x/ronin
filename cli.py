import typer
from agent import Agent

app = typer.Typer()


@app.command()
def run(task: str):

    agent = Agent()

    agent.run(task)


if __name__ == "__main__":
    app()