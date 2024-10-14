import random
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import authentication
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from articles.models import Article, Rating
from articles.constants import RatingScores, RatingSpamStatus
authentication.TokenAuthentication
from articles.spam_detector import SpamDetector
from articles.spam_handlers.normal_dist_spam_handler import NormalDistProbableSpamHandler
from core.utils import calculate_new_normal_dist_info_with_new_data_points

deactivated_spam_detector = SpamDetector(
    False, 10, 2, None
)


class TestArticlesListView(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username='user1')
        self.article1 = Article.objects.create(title='article1', body='foo')
        self.article2 = Article.objects.create(title='article2', body='foo')
        token, _ = Token.objects.get_or_create(user=self.user)
        self.token = token.key
        self.rating = Rating.objects.create(
            score=RatingScores.TWO,
            user=self.user,
            article=self.article1,
            spam_status=RatingSpamStatus.NOT_SPAM
        )

    def test_api_call_should_return_articles_list_with_correct_user_ratings_when_user_is_authenticated(self):
        url = reverse('articles-list')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(data['results'][0]['user_rating'], None)
        self.assertEqual(data['results'][1]['user_rating'], self.rating.score)
        self.client.credentials()

    def test_api_call_should_return_articles_list_in_decreasing_created_at_order(self):
        url = reverse('articles-list')
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'][0]['id'], self.article2.id)
        self.assertEqual(data['results'][1]['id'], self.article1.id)


@patch('articles.views.spam_detector', deactivated_spam_detector)
class TestRatingView(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username='user1')
        token, _ = Token.objects.get_or_create(user=self.user)
        self.token = token.key

        self.article_without_rating = Article.objects.create(title='article2', body='foo')
        self.initial_score = RatingScores.TWO
        self.article_with_rating = Article.objects.create(
            title='article1',
            body='foo',
            rating_count=1,
            rating_average=self.initial_score,
            rating_square_sum=0.0
        )
        self.rating = Rating.objects.create(
            score=self.initial_score,
            user=self.user,
            article=self.article_with_rating,
            spam_status=RatingSpamStatus.NOT_SPAM
        )

    def test_api_call_should_return_401_status_code_when_user_is_not_authenticated(self):
        url = reverse('create-rating')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_call_should_create_rating_when_user_has_no_previous_rating_on_article(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('create-rating')
        score = 1
        response = self.client.post(
            url,
            data={
                'score': score,
                'article': self.article_without_rating.id
            }
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rating_id = data['rating']['id']
        rating = Rating.objects.filter(id=rating_id).first()
        self.assertNotEqual(rating_id, self.rating.id)
        self.assertIsNotNone(rating)
        self.assertEqual(rating.score, score)
        self.assertEqual(rating.user_id, self.user.id)
        self.assertEqual(rating.article_id, self.article_without_rating.id)
        self.article_without_rating.refresh_from_db()
        self.assertEqual(self.article_without_rating.rating_count, 1)
        self.assertEqual(self.article_without_rating.rating_average, score)

    def test_api_call_should_update_rating_when_user_has_previous_rating_on_article(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('create-rating')
        score = 0
        response = self.client.post(
            url,
            data={
                'score': 0,
                'article': self.article_with_rating.id
            }
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rating_id = data['rating']['id']

        self.rating.refresh_from_db()
        self.assertEqual(rating_id, self.rating.id)
        self.assertEqual(self.rating.score, score)
        self.article_with_rating.refresh_from_db()
        self.assertEqual(self.article_with_rating.rating_count, 1)
        self.assertEqual(self.article_with_rating.rating_average, score)


class TestSpamDetector(TestCase):

    def setUp(self) -> None:
        self.spam_detector = SpamDetector(
            is_active=True,
            decision_count_limit=100,
            normal_zscore_bound=2,
            probable_spam_handler=None
        )

    def test_get_spam_status_for_score_should_return_probable_spam_when_score_is_out_of_bound(self):
        spam_status = self.spam_detector.get_spam_status_for_score(0, 101, 4.5, 4)
        self.assertEqual(spam_status, RatingSpamStatus.PROBABLE_SPAM)

    def test_get_spam_status_for_score_should_return_not_spam_when_is_not_active(self):
        self.spam_detector.is_active = False
        spam_status = self.spam_detector.get_spam_status_for_score(0, 101, 4.5, 4)
        self.assertEqual(spam_status, RatingSpamStatus.NOT_SPAM)
        self.spam_detector.is_active = True

    def test_get_spam_status_for_score_should_return_not_spam_when_rating_count_is_less_than_limit(self):
        spam_status = self.spam_detector.get_spam_status_for_score(0, 99, 4.5, 4)
        self.assertEqual(spam_status, RatingSpamStatus.NOT_SPAM)

    def test_get_spam_status_for_score_should_return_not_spam_when_variance_is_0(self):
        spam_status = self.spam_detector.get_spam_status_for_score(0, 101, 4.5, 0)
        self.assertEqual(spam_status, RatingSpamStatus.NOT_SPAM)


class TestNormalDistProbableSpamHandler(TestCase):

    def setUp(self) -> None:
        self.initial_average = 3.0
        self.initial_count = 100
        self.initial_square_sum = 200.0
        self.article1 = Article.objects.create(
            title='article1',
            body='foo',
            rating_count=self.initial_count,
            rating_average=self.initial_average,
            rating_square_sum=self.initial_square_sum
        )
        self.article2 = Article.objects.create(
            title='article2',
            body='foo',
            rating_count=self.initial_count,
            rating_average=self.initial_average,
            rating_square_sum=self.initial_square_sum
        )

        self.clean_article = Article.objects.create(
            title='article2',
            body='foo'
        )

    def make_normal_dist_ratings_for_article(self, article: Article):
        ratings = []
        ratings += self.make_ratings(0, RatingSpamStatus.NOT_SPAM, article, 5)
        ratings += self.make_ratings(1, RatingSpamStatus.NOT_SPAM, article, 7)
        ratings += self.make_ratings(2, RatingSpamStatus.NOT_SPAM, article, 8)
        ratings += self.make_ratings(3, RatingSpamStatus.NOT_SPAM, article, 20)
        ratings += self.make_ratings(4, RatingSpamStatus.NOT_SPAM, article, 35)
        ratings += self.make_ratings(5, RatingSpamStatus.NOT_SPAM, article, 25)
        scores = [r.score for r in ratings]
        article.update_rating_info_with_new_scores(scores)
        article.refresh_from_db()

    def make_ratings(self, score, spam_status, article, count):
        ratings = []
        for _ in range(count):
            ratings.append(
                Rating.objects.create(
                    user=User.objects.create(username=str(uuid4())),
                    article=article,
                    score=score,
                    spam_status=spam_status,
                )
            )
        return ratings

    def make_ratings_with_random_scores(self, spam_status, article, count):
        ratings = []
        for _ in range(count):
            ratings.append(
                Rating.objects.create(
                    user=User.objects.create(username=str(uuid4())),
                    article=article,
                    score=random.choice([0, 1, 2, 3, 4, 5]),
                    spam_status=spam_status,
                )
            )
        return ratings

    def assert_article_rating_info_is_as_expected(
            self,
            article: Article,
            expected_average: float,
            expected_count: int,
            expected_mean_diff_square_sum: float,
    ):
        self.assertEqual(article.rating_average, expected_average)
        self.assertEqual(article.rating_count, expected_count)
        self.assertAlmostEqual(article.rating_square_sum, expected_mean_diff_square_sum, 3)

    def test_handle_not_spam_ratings_should_update_multiple_articles_rating_info_and_ratings_spam_status(self):
        article1_ratings = self.make_ratings_with_random_scores(RatingSpamStatus.PROBABLE_SPAM, self.article1, 10)
        article2_ratings = self.make_ratings_with_random_scores(RatingSpamStatus.PROBABLE_SPAM, self.article2, 10)

        ratings = article1_ratings + article2_ratings
        rating_ids = [rating.id for rating in ratings]
        noraml_dist_probable_spam_handler = NormalDistProbableSpamHandler(0.1)
        noraml_dist_probable_spam_handler.handle_not_spam_ratings(rating_ids)

        expected_values_of_article1 = calculate_new_normal_dist_info_with_new_data_points(
            self.initial_average, self.initial_square_sum, self.initial_count, [r.score for r in article1_ratings]
        )
        expected_values_of_article2 = calculate_new_normal_dist_info_with_new_data_points(
            self.initial_average, self.initial_square_sum, self.initial_count, [r.score for r in article2_ratings]
        )

        expected_average, expected_sum_of_square, expected_count = expected_values_of_article1
        self.article1.refresh_from_db()
        self.assert_article_rating_info_is_as_expected(
            self.article1,
            expected_average,
            expected_count,
            expected_sum_of_square,
        )
        expected_average, expected_sum_of_square, expected_count = expected_values_of_article2
        self.article2.refresh_from_db()
        self.assert_article_rating_info_is_as_expected(
            self.article2,
            expected_average,
            expected_count,
            expected_sum_of_square,
        )

        ratings = list(Rating.objects.filter(id__in=rating_ids))
        for rating in ratings:
            self.assertEqual(rating.spam_status, RatingSpamStatus.NOT_SPAM)

    def test_handle_spam_ratings_should_update_ratings_spam_status(self):
        ratings = self.make_ratings_with_random_scores(RatingSpamStatus.PROBABLE_SPAM, self.article1, 10)

        noraml_dist_probable_spam_handler = NormalDistProbableSpamHandler(0.1)
        rating_ids = [rating.id for rating in ratings]
        noraml_dist_probable_spam_handler.handle_spam_ratings(rating_ids)

        self.article1.refresh_from_db()
        self.assert_article_rating_info_is_as_expected(
            self.article1,
            self.initial_average,
            self.initial_count,
            self.initial_square_sum,
        )

        ratings = list(Rating.objects.filter(id__in=rating_ids))
        for rating in ratings:
            self.assertEqual(rating.spam_status, RatingSpamStatus.SPAM)

    def test_handle_should_detect_and_update_spam_ratings_when_diff_prob_limit_is_exceeded(self):
        self.make_normal_dist_ratings_for_article(self.clean_article)

        expected_average = self.clean_article.rating_average
        expected_count = self.clean_article.rating_count
        expected_mean_diff_square_sum = self.clean_article.rating_square_sum

        spam_ratings = self.make_ratings(0, RatingSpamStatus.PROBABLE_SPAM, self.clean_article, 10)
        probable_spam_handler = NormalDistProbableSpamHandler(0.1)
        probable_spam_handler.handle()

        for r in spam_ratings:
            r.refresh_from_db()
            self.assertEqual(r.spam_status, RatingSpamStatus.SPAM)

        self.clean_article.refresh_from_db()
        self.assert_article_rating_info_is_as_expected(
            self.clean_article,
            expected_average,
            expected_count,
            expected_mean_diff_square_sum,
        )

    def test_handle_should_detect_and_update_spam_ratings_and_articles_when_diff_prob_is_below_limit(self):
        self.make_normal_dist_ratings_for_article(self.clean_article)
        expected_data = calculate_new_normal_dist_info_with_new_data_points(
            self.clean_article.rating_average,
            self.clean_article.rating_square_sum,
            self.clean_article.rating_count,
            [0, 0, 0, 0, 0]
        )
        expected_average, expected_mean_diff_square_sum, expected_count = expected_data

        spam_ratings = self.make_ratings(0, RatingSpamStatus.PROBABLE_SPAM, self.clean_article, 5)
        probable_spam_handler = NormalDistProbableSpamHandler(0.1)
        probable_spam_handler.handle()

        for r in spam_ratings:
            r.refresh_from_db()
            self.assertEqual(r.spam_status, RatingSpamStatus.NOT_SPAM)

        self.clean_article.refresh_from_db()
        self.assert_article_rating_info_is_as_expected(
            self.clean_article,
            expected_average,
            expected_count,
            expected_mean_diff_square_sum,
        )
