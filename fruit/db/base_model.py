from django.db import models

class BaseModel(models.Model):
    '''abstrate class'''

    create_time = models