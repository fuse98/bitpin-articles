from core.celery import celery_app
from articles.spam_detector import spam_detector

@celery_app.task
def handle_probable_spam_ratings():
    spam_detector.handle_probable_spams()
