import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from venroy_crawler.items import VenroyItem


class VenroySpider(CrawlSpider):
    name = 'venroy_spider'
    allowed_domains = ["venroy.com.au"]
    start_urls = [
        'https://venroy.com.au',
    ]

    custom_settings = {
        'CLOSESPIDER_ITEMCOUNT': 100,
    }

    rules = [
        Rule(
            LinkExtractor(
                deny=(
                    'pages',
                    'account',
                    'a/returns',
                    'shop-new',
                    'shop-all',
                    'sweaters',
                    'venroyfromhome',
                    'venroy-beach-club',
                    'spring-18',
                    'final-few',
                    'gift-card',
                ),
                canonicalize=True,
                unique=True
            ),
            follow=True,
            callback="parse_items"
        ),

    ]

    # Method which starts the requests by visiting all URLs specified in start_urls
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def parse_items(self, response):
        # The list of products defined by name and colour, for further uniqueness check
        items = []
        # Only extract canonicalized and unique links (with respect to the current page)
        links = LinkExtractor(allow='products/', canonicalize=True, unique=True).extract_links(response)
        # Go through all the links found
        for link in links:
            if len(items) > 100:
                break
            else:
                # Check whether the domain of the URL of the link is allowed; so whether it is in one of the allowed domains
                for domain in self.allowed_domains:
                    if domain in link.url:
                        # Get response from product page
                        product_name = response.xpath('//*[@class="product-single__title"]/text()').get()
                        if product_name:
                            # Extract the colour of the product to merge it with product name and check for uniqueness
                            colour = response.xpath('//*[@class="color-img active"]/@alt').get()
                            unique_product = product_name + "_" + colour
                            if unique_product not in items:
                                # If this particular product hasn't been scraped yet it's added to items list and
                                # its instance with respective fields is created
                                items.append(unique_product)
                                item = VenroyItem()
                                item['colour'] = colour
                                item['product_name'] = product_name
                                item['price'] = response.xpath(
                                    '//*[@id="ProductPrice-product-template"]/@content').get()
                                item['currency'] = response.xpath(
                                    '//*[@class="current-currency"]/span/text()').get().strip("$")
                                image_urls = response.xpath(
                                        '//*[@class="product-single__photos-desktop"]/img/@src').extract()
                                item['image_urls'] = ">>".join(["https:" + url for url in image_urls])

                                # As products description has various location and structure at different pages
                                # I've implemented rather bulky approach in order to gather it into one field
                                description_passage = response.xpath(
                                    '//*[@id="shopify-section-product-template"]/comment()').get()
                                description_start = description_passage.find("</strong>") + 9
                                description_end_fabric = description_passage.find("Fabric")
                                description_end_worn = description_passage.find("Worn")
                                description_end_size = description_passage.find("Size")

                                if 0 < description_end_worn < description_end_fabric:
                                    description_end = description_end_worn
                                elif description_end_worn < 0 and description_end_fabric < 0:
                                    description_end = description_end_size
                                else:
                                    description_end = description_end_fabric

                                description = description_passage[description_start:description_end].\
                                    replace("<br>", "").\
                                    replace("<strong>", "").\
                                    replace("<span>", "").\
                                    replace("</strong>", "").\
                                    replace('<meta charset="utf-8">', "").\
                                    replace("<p>", "").\
                                    replace("</p>", "").\
                                    replace("/span", "").\
                                    replace("<>", "").\
                                    replace("</em>", "").\
                                    strip()

                                if response.xpath(
                                        '//*[@class="product-single__description rte"]/ul/li/text()').extract():
                                    additional_info = "".join(["\n - " + item for item in response.xpath(
                                        '//*[@class="product-single__description rte"]/ul/li/text()').extract()
                                                               if item != "\n"])
                                    item['description'] = description + additional_info
                                else:
                                    item['description'] = description

                                yield item
