import abc
import logging

logger = logging.getLogger(__name__)


class BaseProbableSpamHandler(abc.ABC):

    def detect_real_spam_ratings(self, ratings):
        raise NotImplementedError()

    def get_suspicouse_ratings(self):
        raise NotImplementedError()

    def handle_not_spam_ratings(self, not_spam_rating_ids):
        raise NotImplementedError()

    def handle_spam_ratings(self, spam_rating_ids):
        raise NotImplementedError()

    def handle(self):
        probable_spam_ratings = self.get_suspicouse_ratings()
        spam_rating_ids, not_spam_rating_ids = self.detect_real_spam_ratings(probable_spam_ratings)
        self.handle_not_spam_ratings(not_spam_rating_ids)
        self.handle_spam_ratings(spam_rating_ids)
        logger.info(
            'Ran Spam Rating Handler',
            extra={
                'spam_ratings_count': len(spam_rating_ids),
                'not_spam_ratings_count': len(not_spam_rating_ids),
            }
        )
