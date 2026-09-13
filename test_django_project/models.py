from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()

    def publish(self):
        self.save(force_insert=True)