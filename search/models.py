from elasticsearch_dsl import DocType, Completion, Text, Date, Keyword, Integer

from elasticsearch_dsl.connections import connections
connections.create_connection(host=["localhost"])


# Create your models here.
class ArticleType(DocType):
    suggest = Completion(analyzer="ik_max_word")
    title = Text(analyzer="ik_max_word")
    create_date = Date()
    url = Keyword()
    url_object_id = Keyword()
    front_image_url = Keyword()
    front_image_path = Keyword()
    praise_nums = Integer()
    comment_nums = Integer()
    fav_nums = Integer()
    tags = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_max_word")

    class Meta:
        index = "jobbole"
        doc_type = "article"

if __name__ == "__main__":
    ArticleType.init()