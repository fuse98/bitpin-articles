from rest_framework import serializers

from articles.models import Article, Rating

class ArticleForListSerializer(serializers.ModelSerializer):
    user_rating = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Article
        exclude = ['rating_square_sum']


class RatingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Rating
        exclude = ['spam_status', 'user',]
