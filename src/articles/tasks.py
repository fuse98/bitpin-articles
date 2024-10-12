from core.celery import celery_app
from articles.spam_handlers import NormalDistributionSpamRatingHandler

@celery_app.task
def handle_probable_spam_ratings():
    probable_spam_handler = NormalDistributionSpamRatingHandler()
    probable_spam_handler.handle()
