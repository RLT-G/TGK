from django.db import models
from django.utils import timezone
from .tasks import connect_telegram_account
from multiselectfield import MultiSelectField


class Proxy(models.Model):
    IPVERSIONS = [
        ('6', 'IPv6'),
        ('4', 'IPv4'),
    ]
    id = models.CharField(primary_key=True, max_length=255)
    version = models.CharField('Версия прокси', max_length=50, choices=IPVERSIONS)
    ip = models.GenericIPAddressField('Прокси IP')
    host = models.CharField('Хост (Для подключения)', max_length=255)
    port = models.CharField('Порт (Для подключения)', max_length=10)
    user = models.CharField('Логин (Для подключения)', max_length=255)
    password = models.CharField('Пароль (Для подключения)', max_length=255)
    date = models.DateTimeField('Дата покупки')
    date_end = models.DateTimeField('Дата завершения')
    active = models.BooleanField('Прокси активна?', default=True)
    country = models.CharField('Страна', max_length=100)
    is_linked = models.BooleanField('Подключен к аккаунту?', default=False)

    class Meta:
        managed = False 
        db_table = 'proxies'
        verbose_name = 'Прокси-сервер'
        verbose_name_plural = 'Прокси-сервера'

    def __str__(self):
        return f"{str(self.country).upper()} --- {self.ip}"


class PhoneNumber(models.Model):
    number = models.CharField('Номер телефона (+7XXXXXXXXXX)', max_length=20, unique=True)
    country = models.CharField('Страна', max_length=100)
    is_used = models.BooleanField('Номер связан с аккаунтом?', default=False)
    received_code = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        managed = False 
        db_table = 'phone_numbers'
        verbose_name = 'Номер телефона'
        verbose_name_plural = 'Номера телефонов'

    def __str__(self):
        return f"{str(self.country).upper()} --- {self.number}"


class Order(models.Model):
    CATEGORY = [
        ('news', 'Новости и СМИ'),
        ('entertrainment', 'Юмор и развлечение'),
        ('blogs', 'Блоги'),
        ('technologies', 'Технологии'),
        ('policy', 'Политика'),
        ('crypto', 'Крипта'),
        ('films|TV', 'Фильмы и сериалы'),
        ('education', 'Наука и образование'),
        ('economy', 'Экономика и финансы'),
        ('music', 'Музыка'),
        ('linguistics', 'Лингвистика'),
        ('business', 'Бизнес и стартапы'),
        ('psychology', 'Психология'),
        ('marketing', 'Маркетинг и реклама'),
        ('career', 'Карьера'),
        ('literature', 'Литература'),
        ('sport', 'Спорт и здоровье'),
        ('trips', 'Путешествия'),
        ('art', 'Искусство и фото'),
        ('fashion', 'Мода и красота'),
        ('medicine', 'Медицина'),
        ('games', 'Игры и приложения'),
        ('food', 'Еда и напитки'),
    ]
    
    STATUSES = [
        ('pending', 'В очереди'),
        ('active', 'Активный'),
        ('completed', 'Завершен'),
    ]

    statuses_for_str = {
        'pending': 'В очереди',
        'active': 'Активный',
        'completed': 'Завершен',
    }

    created_at = models.DateTimeField('Дата создания', default=timezone.now)
    channel_address = models.CharField('Рекламируемый канал (@example или https://t.me/example)')
    channel_description = models.TextField('Описание рекламируемого канала', max_length=70, null=True, blank=True)
    channel_category = MultiSelectField(
        'Категория рекламируемого канала',
        max_length=255,
        choices=CATEGORY,
        max_choices=4,
    )

    ordered_comment_posts = models.IntegerField('Заказанное кол-во комментариев', null=True, blank=True)
    completed_comment_posts = models.IntegerField('Выполненное кол-во комментариев', default=0, null=True, blank=True)
    
    ordered_ad_days = models.IntegerField('Заказанное кол-во дней рекламирования', null=True, blank=True)
    completed_ad_days = models.IntegerField('Выполненное кол-во дней рекламирования', default=0, null=True, blank=True)
    
    accounts_count = models.IntegerField('Кол-во аккаунтов для комментирования', default=0)
    ordered_status = models.CharField('Статус заказа', choices=STATUSES, default='pending')
    is_active = models.BooleanField('Заказ активен?', default=False)
    
    class Meta:
        managed = False 
        db_table = 'orders'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
    
    def __str__(self):
        return f"Заказ №{self.pk} --- {self.channel_address} --- {self.statuses_for_str.get(self.ordered_status)} "


class TelegramAccount(models.Model):
    CATEGORY = [
        ('F', 'Женский'),
        ('M', 'Мужской'),
    ]

    username = models.CharField('Имя пользователя (@username)', max_length=100, unique=True, null=True, blank=True)
    phone_number = models.OneToOneField(PhoneNumber, on_delete=models.CASCADE, verbose_name='Номер телефона', )
    proxy = models.OneToOneField(Proxy, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Прокси-сервер')
    gender = models.CharField('Пол', max_length=1, choices=CATEGORY)
    description = models.TextField('Описание аккаунта', null=True, blank=True, default='')
    is_banned = models.BooleanField('Аккаунт забанен?', default=False)
    created_at = models.DateTimeField('Дата создания', default=timezone.now)
    api_id = models.CharField('Api id аккаунта', null=False)
    api_hash = models.CharField('Api hash аккаунта', null=False)
    is_searcher = models.BooleanField('Использовать аккаунт для парсинга?', default=False)
    is_connected = models.BooleanField('Аккаунт авторизирован в системе?', default=False)
    auth_code = models.CharField('Код подтверждения', max_length=255, null=True, blank=True)
    current_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Текущий заказ')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, db_column='avatar_url', verbose_name='Аватар')

    class Meta:
        managed = False 
        db_table = 'telegram_accounts'
        verbose_name = 'ТГ аккаунт'
        verbose_name_plural = 'ТГ аккаунты'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            connect_telegram_account.delay(self.id)
        


    def __str__(self):
        return self.username or str(self.phone_number)





class Channel(models.Model):
    CATEGORY = [
        ('news', 'Новости и СМИ'),
        ('entertrainment', 'Юмор и развлечение'),
        ('blogs', 'Блоги'),
        ('technologies', 'Технологии'),
        ('policy', 'Политика'),
        ('crypto', 'Крипта'),
        ('films|TV', 'Фильмы и сериалы'),
        ('education', 'Наука и образование'),
        ('economy', 'Экономика и финансы'),
        ('music', 'Музыка'),
        ('linguistics', 'Лингвистика'),
        ('business', 'Бизнес и стартапы'),
        ('psychology', 'Психология'),
        ('marketing', 'Маркетинг и реклама'),
        ('career', 'Карьера'),
        ('literature', 'Литература'),
        ('sport', 'Спорт и здоровье'),
        ('trips', 'Путешествия'),
        ('art', 'Искусство и фото'),
        ('fashion', 'Мода и красота'),
        ('medicine', 'Медицина'),
        ('games', 'Игры и приложения'),
        ('food', 'Еда и напитки'),
    ]

    telegram_link = models.URLField('URL канала', unique=True)
    category = models.CharField('Категория канала', max_length=50, choices=CATEGORY, null=False, blank=False)

    class Meta:
        managed = False 
        db_table = 'channels'
        verbose_name = 'Канал'
        verbose_name_plural = 'Каналы'

    def __str__(self):
        return f"№{self.pk}. {self.telegram_link}"
    

class Comment(models.Model):
    telegram_account = models.ForeignKey(TelegramAccount, on_delete=models.CASCADE, verbose_name='Телеграмм аккаунт')
    channel_link = models.URLField('URL канала')
    comment_link = models.CharField('URL комментария', max_length=100, null=True, blank=True)#Column(String(100), nullable=True)
    text = models.TextField('Текст комментария')
    posted_at = models.DateTimeField('Дата размещения', default=timezone.now)

    class Meta:
        managed = False 
        db_table = 'comments'
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f"Аккаунт: {self.telegram_account.username} | URL канала: {self.channel_link} | URL комментария: {self.comment_link or 'unknown'}"
