from typing import List

from django.db import models
from django.contrib.auth.models import User

from articles.managers import RatingManager, ArticleManager
from articles.constants import RatingScores, RatingSpamStatus
from core.settings import config
from core.utils import (
    calculate_new_normal_dist_info_with_data_update,
    calculate_new_normal_dist_info_with_new_data_points
)


class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    rating_count = models.BigIntegerField(default=0)
    rating_average = models.FloatField(default=0)
    rating_square_sum = models.FloatField(default=0.0)

    objects: ArticleManager = ArticleManager()

    def get_variance(self) -> float:
        if self.rating_count == 0:
            return 0.0

        return self.rating_square_sum / self.rating_count

    def update_rating_info_with_rating(self, rating, old_score: int|None=None) -> None:
        if rating.spam_status != RatingSpamStatus.NOT_SPAM:
            return
        if old_score is None:
            self.update_rating_info_with_new_scores(new_scores=[rating.score])
        else:
            self.update_rating_info_with_updated_score(rating.score, old_score)

    def update_rating_info_with_updated_score(self, score, old_score):
        new_mean, new_sum_squares =calculate_new_normal_dist_info_with_data_update(
            models.F('rating_average'),
            models.F('rating_square_sum'),
            models.F('rating_count'),
            score,
            old_score,
        )
        self.rating_average = new_mean
        self.rating_square_sum = new_sum_squares
        self.save()

    def update_rating_info_with_new_scores(self, new_scores: List[int]) -> None:
        new_mean, new_sum_squares, new_count = calculate_new_normal_dist_info_with_new_data_points(
            models.F('rating_average'),
            models.F('rating_square_sum'),
            models.F('rating_count'),
            new_scores
        )

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
