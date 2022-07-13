import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from venroy_crawler.items import VenroyLoader


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
                    'knitwear',
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
                # Check whether the domain of the URL of the link is allowed; so whether it is in one of the allowed
                # domains
                for domain in self.allowed_domains:
                    if domain in link.url:
                        # Get response from product page
                        product_title = response.xpath('//title/text()').get()
                        product_name = response.xpath('//*[@class="handle__Heading-sc-hd87fs-0 lKRSl"]/text()').get()
                        if product_name and product_title not in items:
                            # If this particular product hasn't been scraped yet it's added to items list and
                            # its instance with respective fields is created
                            items.append(product_title)
                            loader = VenroyLoader(selector=response)
                            title_name = product_title.split("|")[0]
                            title_colour = title_name.split(" in ")[1]
                            loader.add_value('product_name', product_name)
                            loader.add_value('colour', title_colour)
                            # loader.add_xpath('currency', '//*[@class="current-currency"]/span/text()')
                            # loader.add_xpath('price', '//*[@id="ProductPrice-product-template"]/@content')
                            image_url = response.xpath('//*[@property="og:image"]/@content').get().strip("https:")
                            loader.add_value('image_urls', image_url)
                            # As products description has various location and structure at different pages
                            # I've implemented rather bulky approach in order to gather it into one field
                            description_passage = response.xpath(
                                '//*[@class="Accordion__Wrapper-sc-wihakm-3 bMligg accordion active"]/@content').get()
                            description = description_passage.\
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
                                replace("<ul>", "").\
                                replace("</li>", "").\
                                replace("</ul>", "").\
                                replace("<li>", "").\
                                strip()

                            loader.add_value('description', description)

                            yield loader.load_item()
