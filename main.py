"""Chat with the agent in your terminal:  uv run main.py"""

import uuid

from dotenv import load_dotenv

load_dotenv()  # load .env before anything reads the API keys

from langgraph.types import Command  # noqa: E402

from agent.graph import build_graph  # noqa: E402


def main():
    graph = build_graph()
    # One thread_id = one conversation (memory is kept per thread).
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    print("Assistant commercial prêt. Tape 'exit' pour quitter.\n")
    while True:
        question = input("Toi > ").strip()
        if question.lower() in {"exit", "quit", "q"}:
            break
        if not question:
            continue

        graph.invoke({"messages": [("user", question)]}, config)

        # If a tool called interrupt(), the graph is paused: ask the human.
        while (state := graph.get_state(config)).interrupts:
            email = state.interrupts[0].value
            print("\n--- Email à envoyer ---")
            print(f"À      : {email['to']}")
            print(f"Objet  : {email['subject']}")
            print(f"\n{email['body']}\n-----------------------")
            answer = input("Envoyer ? (yes/no) > ").strip().lower()
            graph.invoke(Command(resume=answer), config)

        print(f"\nAgent > {graph.get_state(config).values['messages'][-1].content}\n")


if __name__ == "__main__":
    main()
