from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpResponse

from search.models import ArticleType

import json

# Create your views here.
class IndexView(View):
    def get(self, request):
        return render(request, "index.html")


class SearchView(View):
    def get(self, request):
        return render(request, "result.html")


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

