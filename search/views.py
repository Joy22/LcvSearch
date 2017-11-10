from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpResponse
from elasticsearch import Elasticsearch

from search.models import ArticleType

import json
import redis

redis_cli = redis.StrictRedis()
client = Elasticsearch(hosts=["127.0.0.1"])


# Create your views here.
class IndexView(View):
    def get(self, request):
        # 逆序排列热门搜索，取前5个
        hot_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)
        return render(request, "index.html", {"hot_search": hot_search})


class SearchView(View):
    def get(self, request):
        keyword = request.GET.get("q", "")
        page = request.GET.get("p", "1")
        try:
            page = int(page)
        except:
            page = 1

        # redis关键词加1
        redis_cli.zincrby("search_keywords_set", keyword)

        hot_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)

        response = self.__get_search_response(keyword, page)
        hit_list, total_nums = self.__parse_search_response(response)

        return render(request, "result.html",
                      {"hot_search": hot_search, "all_hits": hit_list, "total_nums": total_nums})

    @staticmethod
    def __get_search_response(keyword, page):
        response = client.search(
            index="jobbole",
            body={
                "query": {
                    "multi_match": {
                        "query": keyword,
                        "field": ["tags", "title", "content"]
                    }
                },
                "from": (page - 1) * 10,
                "size": 10,
                "highlight": {
                    "pre_tags": ['<span class="keyWord>'],
                    "post_tags": ['</span>'],
                    "fields": {
                        "title": {},
                        "content": {}
                    }
                }
            }
        )
        return response

    @staticmethod
    def __parse_search_response(response):
        hit_list = []
        for hit in response["hits"]["hits"]:
            hit_dict = {}
            if "title" in hit["highlight"]:
                hit_dict["title"] = "".join(hit["highlight"]["title"])
            else:
                hit_dict["title"] = hit["_source"]["title"]
            if "content" in hit["highlight"]:
                hit_dict["content"] = "".join(hit["highlight"]["content"])[:500]
            else:
                hit_dict["content"] = hit["_source"]["content"][:500]
            hit_dict["create_date"] = hit["_source"]["create_date"]
            hit_dict["url"] = hit["_source"]["url"]
            hit_dict["score"] = hit["_source"]
            hit_list.append(hit_dict)

        total_nums = response["hits"]["total"]
        return hit_list, total_nums


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
        return HttpResponse(json.dumps(return_data), content_type="application/json")
