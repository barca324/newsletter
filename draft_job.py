import os

if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

from content import fetch_and_generate_post
from emailer import send_draft_email
from image_generator import generate_news_image


def main() -> None:
    print("Searching today's AI news via Gemini...")
    post, takeaway, headlines = fetch_and_generate_post()
    

    image_path = generate_news_image(
      headlines,
      post,
      takeaway,
    )

    print("\n--- DRAFT POST ---")
    print(post)
    print(f"\n--- {len(headlines)} HEADLINES ---\n")

    with open("draft.txt", "w", encoding="utf-8") as f:
        f.write(post)

    print("Sending email...")
    send_draft_email("AInew.in daily draft", post, headlines,image_path)
    print("Done.")


if __name__ == "__main__":
    main()