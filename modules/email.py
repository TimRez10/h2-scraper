# Helper functions for sending the email report

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pretty_html_table import build_table
import pandas as pd

def format_email_html(articles_df):
    # Rename columns
    df = articles_df.rename(columns={
        'title': 'Title',
        'region': 'Region',
        'date_published': 'Date',
        'rel_score': 'Rel Score (out of 100)',
        'h2_mentioned': 'Is H2 mentioned?',
        'tags': 'Tag',
        'link': 'Link',
        'classification': 'Classification',
        'source':'Source'
    })

    # Format date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%B %-d, %Y')  # e.g., July 4, 2025

    # Format "Is H2 mentioned?" column
    df['Is H2 mentioned?'] = df['Is H2 mentioned?'].apply(
        lambda x: f"Yes - {int(x)} times" if pd.notnull(x) and int(x) > 0 else "No"
    )

    # Reorder columns
    desired_order = [
        'Title', 'Region', 'Date', 'Rel Score (out of 100)',
        'Is H2 mentioned?', 'Tag', 'Link', 'Classification', 'Source'
    ]
    df = df[desired_order]

    # Generate HTML
    html_content = build_table(df, 'blue_dark', padding='5px 20px 5px 5px')
    html_content = html_content.replace('font-size: medium', 'font-size: 13px')

    return html_content



def send_email(subject, sender, recipient, msg_string, msg_html, attachment_file_paths, smtp_username, smtp_password, logger=None):
    # Outer container (for attachments)
    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    # Inner container for email body
    alternative_part = MIMEMultipart('alternative')
    text_message = MIMEText(msg_string, 'plain')
    html_message = MIMEText(msg_html, 'html')
    alternative_part.attach(text_message)
    alternative_part.attach(html_message)

    # Attach the alternative part to the main message
    msg.attach(alternative_part)

    # Attach files
    for file_path in attachment_file_paths:
        with open(file_path, "rb") as attachment_file:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment_file.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={file_path.split("/")[-1]}'
            )
            msg.attach(part)

    # Send email
    mailServer = smtplib.SMTP('mail.smtp2go.com', 2525)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(smtp_username, smtp_password)
    mailServer.sendmail(sender, recipient.split("; "), msg.as_string())
    mailServer.close()

    if logger:
        logger.info("Email has been sent to: %s" % recipient)