from django.db import models

# Create your models here.

class Hotel(models.Model):
    name = models.CharField(max_length=500)
    location = models.CharField(max_length=500)
    description = models.CharField(max_length=500)
    average_rating = models.DecimalField(decimal_places=2, max_digits=5)
    average_price = models.CharField(max_length=500)
    features = models.TextField()

    class Meta:
        unique_together = ('name', 'location')

    def __str__(self):
        return self.name

    # def 


class HotelPrice(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    room = models.CharField(max_length=500)
    price = models.CharField(max_length=500) #charfield to capture currency
    # currency = models.CharField(max_length=500)
    # price = models.DecimalField(decimal_places=2, max_digits=20)
    availability = models.IntegerField()
    # average_rating = models.IntegerField()
    scrape_date = models.DateTimeField(auto_now_add=True)  # change to date field
    date_added = models.DateField(auto_now_add=True)

    # class Meta:
    #     unique_together = ('hotel', 'date_added')

    def __str__(self):
        return f"{self.hotel} - {self.price}"
    
    @property
    def strip_price(self):
        try:
            return int(self.price[1:])
        except ValueError:
            return 0


class HotelReview(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=5, decimal_places=2)
    review = models.TextField()

    def __str__(self):
        return f"{self.hotel} - {self.rating}"

    def striped_review(self):
        return True

