from django.db import models
from django.contrib.auth.models import User

from articles.managers import RatingManager, ArticleManager
from articles.constants import RatingScores, RatingSpamStatus
from core.settings import config
from core.utils import calculate_zscore


class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    rating_count = models.BigIntegerField(default=0)
    rating_average = models.FloatField(default=0)
    rating_square_sum = models.BigIntegerField(default=0)

    objects: ArticleManager = ArticleManager()

    def get_variance(self) -> float:
        return self.rating_square_sum / self.rating_count

    def update_rating_info_with_rating(self, rating, old_score: int|None=None) -> None:
        if rating.spam_status != RatingSpamStatus.NOT_SPAM:
            return
        if old_score is None:
            self.update_rating_info_with_new_scores(rating.score, 1)
        else:
            self.update_rating_info_with_updated_score(rating.score, old_score)

    def update_rating_info_with_updated_score(self, score, old_score):
        count = models.F('rating_count')
        old_mean = models.F('rating_average')
        old_sum_squares = models.F('rating_square_sum')

        new_mean = ((old_mean * count) + (score - old_score))/count

        mean_change_effect = count * (new_mean - old_mean)**2
        score_change_effect = (score - new_mean)**2 - (old_score - new_mean)**2
        new_sum_squares = old_sum_squares + mean_change_effect + score_change_effect

        self.rating_average = new_mean
        self.rating_square_sum = new_sum_squares
        self.save()

    def update_rating_info_with_new_scores(self, score_sum: int, new_ratings_count: int) -> None:
        old_count = models.F('rating_count')
        old_mean = models.F('rating_average')
        old_sum_squares = models.F('rating_square_sum')

        new_count = old_count + new_ratings_count
        new_mean = (old_mean * old_count + score_sum)/new_count

        d1 = score_sum - old_mean
        d2 = score_sum - new_mean
        new_sum_squares = old_sum_squares + d1*d2

        self.rating_average = new_mean
        self.rating_count = new_count
        self.rating_square_sum = new_sum_squares
        self.save()


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    score = models.SmallIntegerField(choices=RatingScores.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    

    spam_status = models.SmallIntegerField(choices=RatingSpamStatus.choices)

    objects: RatingManager = RatingManager() 

    class Meta:
        unique_together = ('article', 'user',)

    def update_score(self, article: Article, new_score: int):
        self.score = new_score
        self.save()
        return self
