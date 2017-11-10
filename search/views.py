from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpResponse

from search.models import ArticleType

import json
import redis

redis_cli = redis.StrictRedis()

# Create your views here.
class IndexView(View):
    def get(self, request):
        return render(request, "index.html")


class SearchView(View):
    def get(self, request):
        key_word = request.GET.get("q", "")

        # redis关键词加1
        redis_cli.zincrby("search_keywords_set", key_word)

        # 逆序排列热门搜索，取前5个
        hot_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)

        return render(request, "result.html", {"hot_search": hot_search})


class SearchSuggestView(View):
    def get(self, request):
        key_words = request.GET.get("s", "")
        return_data = []
        if key_words:
            s = ArticleType.search()
            s = s.suggest("article_suggest", key_words, completion={
                "field": "suggest",
                "fuzzy": {
                    "fuzziness": 2
                },
                "size": 10
            })
            suggestions = s.execute_suggest()
            for match in suggestions.article_suggest[0].options:
                source = match._source
                return_data.append(source["title"])
        return  HttpResponse(json.dumps(return_data), content_type="application/json")

