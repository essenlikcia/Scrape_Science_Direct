from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=250)
    orcid_id = models.CharField(max_length=200, null=True, blank=True)


class Record(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=500)
    authors = models.ManyToManyField(Author)
    corresponding_author = models.CharField(max_length=250)
    corresponding_author_email = models.EmailField(max_length=250)
    date = models.DateField()
    pii = models.CharField(max_length=250, default="N/A")

    def __str__(self):
        return (f"{self.title} - {self.authors} - {self.corresponding_author} - "
                f"{self.corresponding_author_email} - {self.date}")
