import logging
from typing import List

from django.db import models

from articles.constants import RatingSpamStatus

logger = logging.getLogger(__name__)


class ArticleManager(models.Manager):

    def bulk_update_rating_info(self, articles_rating_info: dict):
        article_ids = articles_rating_info.keys()
        articles = self.filter(id__in=article_ids)
        for article in articles:
            article.update_rating_info_with_new_score(
                score_sum=articles_rating_info[article.id]['score_sum'],
                ratings_count=articles_rating_info[article.id]['ratings_count']
            )

    def get_ratings_score_count_for_article_ids(self, article_ids: List[int]) -> dict:
        articles_score_counts = self.filter(id__in=article_ids).annotate(
            count_0=models.Count('rating__id', filter=models.Q(rating__score=0)),
            count_1=models.Count('rating__id', filter=models.Q(rating__score=1)),
            count_2=models.Count('rating__id', filter=models.Q(rating__score=2)),
            count_3=models.Count('rating__id', filter=models.Q(rating__score=3)),
            count_4=models.Count('rating__id', filter=models.Q(rating__score=4)),
            count_5=models.Count('rating__id', filter=models.Q(rating__score=5)),
        ).values('id', 'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5')
        return {
            d.pop('id'): d for d in articles_score_counts
        }


class RatingManager(models.Manager):

    def get_user_rating_on_article_or_none(self, user, article) -> bool:
        return self.filter(user=user, article=article).last()

    def get_probable_spam_ratings(self):
        return self.filter(spam_status=RatingSpamStatus.PROBABLE_SPAM).prefetch_related('article')

    def create_rating(self, user, article, score: int):
        spam_status = RatingSpamStatus.NOT_SPAM
        if article.score_is_out_of_normal_bound(score):
            spam_status = RatingSpamStatus.PROBABLE_SPAM

        return self.create(
            user=user,
            article=article,
            score=score,
            spam_status=spam_status,
        )

    def annotate_articles_with_user_rating(self, articles, user):
        article_ids = [a.id for a in articles]
        user_ratings = self.filter(
            user=user,
            article_id__in=article_ids
        ).values('article_id', 'score')
        user_ratings_dict = {
            user_rating['article_id']: user_rating['score'] for user_rating in user_ratings
        }
        for a in articles:
            a.__setattr__('user_rating', user_ratings_dict.get(a.id, None))

        return articles

    def get_rating_info_by_articles_for_rating_ids(self, rating_ids: List[int]) -> dict:
        articles_rating_info = self.filter(id__in=rating_ids).values('article_id').annotate(
            ratings_count=models.Count('id'),
            score_sum=models.Sum('score')
        )
        return { i.pop('article_id'): i for i in articles_rating_info}

    def update_spam_status_of_ratings(self, ids, spam_status):
        updated = self.filter(id__in=ids).update(spam_status=spam_status)
        if len(ids) != updated:
            logger.error(
                'Could not update spam_status for all rating ids',
                extra={
                    'rating_count': len(ids),
                    'updated_count': updated,
                    'spam_status': spam_status,
                }
            )
