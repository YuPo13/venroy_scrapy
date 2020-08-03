from scrapy import Item, Field
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose, MapCompose, Join, TakeFirst


class VenroyItem(Item):
    product_name = Field()
    colour = Field()
    price = Field()
    currency = Field()
    image_urls = Field()
    description = Field()


class VenroyLoader(ItemLoader):
    default_item_class = VenroyItem
    image_urls_out = Compose(MapCompose(lambda x: "https:" + x), Join(">>"))
    currency_out = Compose(MapCompose(lambda x: x.strip("$")), TakeFirst())
    price_out = Compose(TakeFirst(), float)

