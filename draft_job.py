import os

if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

from content import fetch_and_generate_post
from emailer import send_draft_email


def main() -> None:
    print("Searching today's AI news via Gemini...")
    post, headlines = fetch_and_generate_post()

    print("\n--- DRAFT POST ---")
    print(post)
    print(f"\n--- {len(headlines)} HEADLINES ---\n")

    with open("draft.txt", "w", encoding="utf-8") as f:
        f.write(post)

    print("Sending email...")
    send_draft_email("AInew.in daily draft", post, headlines)
    print("Done.")


if __name__ == "__main__":
    main()