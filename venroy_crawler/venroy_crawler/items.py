from scrapy import Item, Field


class VenroyItem(Item):
    product_name = Field()
    colour = Field()
    price = Field()
    currency = Field()
    image_urls = Field()
    description = Field()