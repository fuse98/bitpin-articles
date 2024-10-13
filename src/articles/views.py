from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import authentication, permissions

from articles.serializers import ArticleForListSerializer, RatingSerializer
from articles.models import Article, Rating


class ArticlesListView(ListAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Article.objects.order_by('-created_at')

    def get(self, request: Request):
        articles_in_page = self.paginate_queryset(self.get_queryset())
        if request.user.is_authenticated:
            articles_in_page = Rating.objects.annotate_articles_with_user_rating(
                articles_in_page,
                user=request.user
            )

        serializer = ArticleForListSerializer(articles_in_page, many=True)
        return self.get_paginated_response(serializer.data)


class RatingView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request):
        serializer = RatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        article: Article = serializer.validated_data.get('article')
        score = serializer.validated_data.get('score')

        existing_rating: Rating | None = Rating.objects.get_user_rating_on_article_or_none(
            user=request.user, article=article
        )
        if existing_rating is not None:
            old_score = existing_rating.score
            rating = existing_rating.update_score(article, score)
            article.update_rating_info_with_rating(
                rating,
                old_score,
            )
        else:
            rating = Rating.objects.create_rating(
                user=request.user,
                article=article,
                score=score,
            )
            article.update_rating_info_with_rating(rating)

        response_serializer = RatingSerializer(rating)
        return Response(response_serializer.data, status.HTTP_200_OK)
