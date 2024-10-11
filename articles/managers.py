from django.db import models
from articles.constants import RatingSpamStatus

class RatingManager(models.Manager):

    def get_user_rating_on_article_or_none(self, user, article) -> bool:
        return self.filter(user=user, article=article).last()

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
