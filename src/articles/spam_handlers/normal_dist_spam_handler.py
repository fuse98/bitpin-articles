from typing import List
from django.db import transaction

from articles.spam_handlers.base import BaseProbableSpamHandler
from articles.models import Rating, Article
from articles.constants import RatingSpamStatus
from core.utils import calculate_normal_distribution_pdf
from core.settings import config


class NormalDistProbableSpamHandler(BaseProbableSpamHandler):

    def __init__(self, decisive_prob_diff: float) -> None:
        self.decisive_prob_diff = decisive_prob_diff

    def get_suspicouse_ratings(self):
        return Rating.objects.get_probable_spam_ratings()

    def detect_real_spam_ratings(self, ratings: List[Rating]):
        article_ids = [r.article_id for r in ratings]
        article_score_counts_dict= Article.objects.get_ratings_score_count_for_article_ids(article_ids)

        spam_rating_ids = []
        not_spam_rating_ids = []
        for rating in ratings:
            article = rating.article
            score_count = article_score_counts_dict[article.id].get(f'count_{rating.score}')
            real_probability_of_score = score_count / (article.rating_count + score_count)
            normal_pdf = calculate_normal_distribution_pdf(
                article.rating_average,
                article.get_variance(),
                rating.score
            )
            prob_diff = real_probability_of_score - normal_pdf
            if prob_diff > self.decisive_prob_diff:
                spam_rating_ids.append(rating.id)
            else:
                not_spam_rating_ids.append(rating.id)

        return (spam_rating_ids, not_spam_rating_ids)

    def handle_not_spam_ratings(self, not_spam_rating_ids):
        articles_rating_info_dict = Rating.objects.get_rating_info_by_articles_for_rating_ids(
            not_spam_rating_ids
        )
        with transaction.atomic():
            Article.objects.bulk_update_rating_info(
                articles_rating_info_dict
            )
            Rating.objects.update_spam_status_of_ratings(
                not_spam_rating_ids,
                RatingSpamStatus.NOT_SPAM
            )

    def handle_spam_ratings(self, spam_rating_ids):
        Rating.objects.update_spam_status_of_ratings(
            spam_rating_ids,
            RatingSpamStatus.SPAM
        )


normal_dist_probable_spam_handler = NormalDistProbableSpamHandler(
    config.SPAM_RATE_PROB_DIFF_LIMIT
)
