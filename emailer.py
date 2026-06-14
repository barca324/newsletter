import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from email.mime.image import MIMEImage

def send_draft_email(subject: str, post: str, headlines: list[dict],image_path: str | None = None) -> None:
    """Send the draft post + raw headlines to your email via Gmail SMTP."""
    smtp_user = os.environ["GMAIL_USER"]
    smtp_pass = os.environ["GMAIL_APP_PASSWORD"]
    to_email  = os.environ["TO_EMAIL"]

    today = datetime.now().strftime("%d %b %Y")

    headlines_html = "".join(
        f'<li><a href="{h["link"]}">{h["title"]}</a> '
        f'<span style="color:#888">— {h["source"]}, {h["published"]}</span></li>'
        for h in headlines
    )

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:640px;margin:auto">
      <h2 style="color:#0a66c2">AInew.in Daily Draft — {today}</h2>

      <h3>LinkedIn Post</h3>
      <div style="background:#f4f4f4;padding:16px;border-radius:8px;white-space:pre-wrap">{post}</div>

      <h3>Today's Headlines Used</h3>
      <ul>{headlines_html}</ul>

      <hr>
      <p style="color:#888;font-size:12px">Automated by AInew.in · Gemini + Google Search</p>
    </body></html>
    """

    msg = MIMEMultipart()
    msg["Subject"] = f"AInew.in Draft — {today}"
    msg["From"]    = smtp_user
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    if image_path and os.path.exists(image_path):

        with open(image_path, "rb") as f:

           img = MIMEImage(f.read())

        img.add_header(
        "Content-Disposition",
        "attachment",
        filename="daily_news.png"
        )

        msg.attach(img)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())

    print(f"Email sent to {to_email}")