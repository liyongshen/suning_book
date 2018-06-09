# -*- coding: utf-8 -*-
import scrapy
import re
from copy import deepcopy
from suning.items import SuningItem


class SuningbookSpider(scrapy.Spider):
    name = 'suningbook'
    allowed_domains = ["suning.com"]
    start_urls = ["https://book.suning.com/"]

    def parse(self, response):
        # 大分类
        b_type_list = response.xpath("//div[@class = 'menu-item']")
        # 中分类
        m_type_list = response.xpath("//div[@class = 'menu-sub']")

        for node in b_type_list:
            item = SuningItem()
            item["b_type"] = node.xpath(".//h3/a/text()").extract_first()
            # 确定提取某个大分类下的中分类
            index_now = b_type_list.index(node)
            m_type_divs = m_type_list[index_now]
            # 中分类列表
            m_type_list_names = m_type_divs.xpath("./div[1]/p")

            for name in m_type_list_names:
                item["m_type"] = name.xpath("./a/text()").extract_first()
                # 某个中分类中的小分类列表
                s_type_list = name.xpath("./following-sibling::ul[1]/li")

                for s_type_li in s_type_list:
                    # 小分类
                    item["s_type"] = s_type_li.xpath("./a/text()").extract_first()
                    s_type_url = s_type_li.xpath("./a/@href").extract_first()

                    yield scrapy.Request(s_type_url,
                                         callback=self.parse_book_list,
                                         meta={"item": deepcopy(item)}
                                         )

    def parse_book_list(self, response):
        item = response.meta["item"]
        # 两种不同的url的返回结果都可以用下面这种方式提取到当前页书的信息列表
        book_list = response.xpath("//div[@id='filter-results']//li[contains(@class,product)]")
        for book in book_list:
            item["name"] = book.xpath(".//p[@class = 'sell-point']/a/text()").extract_first()
            item["url"] = "https:" + book.xpath(".//p[@class ='sell-point']/a/@href").extract_first()
            yield scrapy.Request(
                item["url"],
                callback=self.book_price,
                meta={"item": deepcopy(item)}
            )

        # 下一页两个ajax请求链接
        book_list1 = 'https://list.suning.com/emall/showProductList.do?ci={}&pg=03&cp={}&il=0&iy=0&adNumber=0&n=1&ch=4&sesab=ABBAAA&id=IDENTIFYING&cc=755'
        book_list2 = 'https://list.suning.com/emall/showProductList.do?ci={}&pg=03&cp={}&il=0&iy=0&adNumber=0&n=1&ch=4&sesab=ABBAAA&id=IDENTIFYING&cc=755&paging=1&sub=0'
        ci = response.url.split("-")[1]

        current_page = re.findall('param\.currentPag.*?"(.*?)"', response.body.decode(), re.S)
        total_page = re.findall('nparam\.pageNumbers.*?"(.*?)"', response.body.decode(), re.S)
        if current_page and total_page:
            if int(current_page[0]) < int(total_page[0]):
                next_page = int(current_page[0]) + 1
                book_list1 = book_list1.format(ci, next_page)
                book_list2 = book_list2.format(ci, next_page)
                yield scrapy.Request(book_list1, callback=self.parse_book_list, meta={"item": item})
                yield scrapy.Request(book_list2, callback=self.parse_book_list, meta={"item": item})

    def book_price(self, response):

        # 'https://pas.suning.com/nspcsale_0_000000000{1}_000000000{1}_{2}_"190_755_7550101_226503_1000051_9051_10346"_{"cmmdtyType"}___{"catenIds"}_{"weight"}.html?callback=pcData&_=1528451505563'

        item = response.meta["item"]
        p1 = response.url.split("/")[-1].split(".")[0]
        p2 = response.url.split("/")[-2]
        p3 = re.findall('"cmmdtyType".*?"(.*?)"', response.body.decode(), re.S)
        p4 = re.findall('"catenIds".*?"(.*?)"', response.body.decode(), re.S)[0]
        p5 = re.findall('"weight".*?"(.*?)"', response.body.decode(), re.S)[0]
        prise_base_url = 'https://pas.suning.com/nspcsale_0_000000000{}_000000000{}_{}_190_755_7550101_226503_1000051_9051_10346_{}___{}_{}.html?callback=pcData&_=1528451505563'
        if p3:
            p3 = p3[0]
            prise_url = prise_base_url.format(p1, p1, p2, p3, p4, p5)
        else:
            prise_url = prise_base_url.format(p1, p1, p2, "", p4, p5)
        yield scrapy.Request(prise_url, callback=self.get_price, meta={"item": item})

    def get_price(self, response):
        item = response.meta["item"]
        item["price"] = re.findall('"netPrice".*?"(.*?)"', response.body.decode(), re.S)[0]

        # 返回item保存
        yield item
