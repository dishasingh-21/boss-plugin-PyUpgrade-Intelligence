from .models import Article


def get_first_article():
    return Article.objects.first()


def publish_first():
    article = get_first_article()   # type comes from a function return, not a direct import
    article.save()                   # this call to Model.save WON'T be detected — this is the limitation in action