import smtplib
from email.mime.text import MIMEText
from apscheduler.schedulers.blocking import BlockingScheduler
from main import run_pipeline

def send_daily_email_digest(new_jobs_count: int):
    """Optional SMTP notification dispatcher."""
    sender_email = "your_email@gmail.com"
    receiver_email = "your_email@gmail.com"
    app_password = "your_app_password"

    msg = MIMEText(f"Public Lead Pipeline Run Complete.\nDiscovered {new_jobs_count} new job leads today.")
    msg['Subject'] = f"🚀 Daily Job Pipeline Digest: {new_jobs_count} New Leads"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("[EMAIL] Daily digest sent successfully.", flush=True)
    except Exception as err:
        print(f"[EMAIL] Skipping digest email (configure SMTP credentials): {err}", flush=True)

def scheduled_job():
    print("\n⏰ Executing Scheduled Lead Extraction Task...", flush=True)
    run_pipeline()

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # Runs Monday-Friday at 08:00 AM
    scheduler.add_job(scheduled_job, 'cron', day_of_week='mon-sun', hour=8, minute=0)
    print("⏰ Job Lead Ingestion Scheduler running (Mon-Sun at 08:00 AM)... Press Ctrl+C to stop.", flush=True)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass