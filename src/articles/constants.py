from django.db import models


class RatingScores(models.IntegerChoices):
    ZERO = 0, 'zero'
    ONE = 1, 'one'
    TWO = 2, 'two'
    THREE = 3, 'three'
    FOUR = 4, 'four'
    FIVE = 5, 'five'


class RatingSpamStatus(models.IntegerChoices):
    NOT_SPAM = 0, 'not spam'
    PROBABLE_SPAM = 1, 'probable spam'
    SPAM = 2, 'spam'
