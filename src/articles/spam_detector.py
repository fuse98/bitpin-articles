from core.settings import config
from core.utils import calculate_zscore
from articles.constants import RatingSpamStatus
from articles.spam_handlers import BaseProbableSpamHandler, normal_dist_probable_spam_handler


class SpamDetector:

    def __init__(
            self,
            is_active: bool,
            decision_count_limit: int,
            normal_zscore_bound: float,
            
            probable_spam_handler: BaseProbableSpamHandler
        ) -> None:
        self.is_active = is_active
        self.decision_count_limit = decision_count_limit
        self.normal_zscore_bound = normal_zscore_bound
        self.probable_spam_handler = probable_spam_handler

    def get_spam_status_for_score(self, score: int, rating_count: int, mean: float, variance: float):
        spam_status = RatingSpamStatus.NOT_SPAM

        if self.is_active and rating_count >= 1 and \
            self.score_is_out_of_normal_bound(score, mean, variance):
            spam_status = RatingSpamStatus.PROBABLE_SPAM

        return spam_status

    def score_is_out_of_normal_bound(self, score: int, mean: float, variance: float):
        print(mean)
        print(variance)
        zscore = calculate_zscore(mean, variance, score)
        return zscore > config.SPAM_RATE_ZSCORE_BOUND or zscore < -1 * config.SPAM_RATE_ZSCORE_BOUND 

    def handle_probable_spams(self):
        self.probable_spam_handler.handle()


spam_detector = SpamDetector(
    is_active=config.SPAM_DETECTION_IS_ACTIVE,
    decision_count_limit=config.SPAM_RATE_COUNT_LIMIT,
    normal_zscore_bound=config.SPAM_RATE_ZSCORE_BOUND,
    probable_spam_handler=normal_dist_probable_spam_handler,
)
