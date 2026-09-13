from .models import Article
from django.core.paginator import Paginator
from django.middleware.locale import LocaleMiddleware
from django.forms.models import BaseModelFormSet
from django.db.models import Model
from django.shortcuts import get_object_or_404
from django.conf import settings

def get_first_article():
    return Article.objects.first()

def paginate_articles(article_list):
    return Paginator(article_list, per_page=10)

def publish_first():
    article = get_first_article()   # type comes from a function return, not a direct import
    article.save()                   # this call to Model.save WON'T be detected — this is the limitation in action

def check_fallback(middleware_instance, request):
    return LocaleMiddleware.get_fallback_language(middleware_instance, request)

def resave(formset_instance, form, obj, commit):
    return BaseModelFormSet.save_existing(formset_instance, form, obj, commit)

def validate_page_number(paginator: Paginator, number):
    return paginator.validate_number(number)

class Articles(Model):
    pass
def create_article():
    return Articles(title="Example")  # MISSED

def check_l10n():
    if settings.USE_L10N:  # MISSED -- no visit_Attribute exists at all
        pass

handler = get_object_or_404
def dispatch(model, pk):
    return handler(model, pk=pk)  # MISSED