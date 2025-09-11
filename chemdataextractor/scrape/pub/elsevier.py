"""
Tools for scraping documents from Elsevier.

:copyright: Copyright 2017 by Callum Court.
:license: MIT, see LICENSE file for more details.
"""

import logging
from time import sleep

from selenium import webdriver

from ...text.normalize import normalize
from ...text.processors import Chain
from ...text.processors import LAdd
from ...text.processors import LStrip
from ...text.processors import RStrip
from ...text.processors import Substitutor
from ..entity import DocumentEntity
from ..entity import Entity
from ..entity import EntityList
from ..fields import EntityField
from ..fields import StringField
from ..fields import UrlField
from ..scraper import UrlScraper
from ..selector import Selector

log = logging.getLogger(__name__)

#: Map placeholder text to unicode characters.
CHAR_REPLACEMENTS = [
    (r"\[?\[1 with combining macron\]\]?", "1\u0304"),
    (r"\[?\[2 with combining macron\]\]?", "2\u0304"),
    (r"\[?\[3 with combining macron\]\]?", "3\u0304"),
    (r"\[?\[4 with combining macron\]\]?", "4\u0304"),
    (r"\[?\[approximate\]\]?", "\u2248"),
    (r"\[?\[bottom\]\]?", "\u22a5"),
    (r"\[?\[c with combining tilde\]\]?", "C\u0303"),
    (r"\[?\[capital delta\]\]?", "\u0394"),
    (r"\[?\[capital lambda\]\]?", "\u039b"),
    (r"\[?\[capital omega\]\]?", "\u03a9"),
    (r"\[?\[capital phi\]\]?", "\u03a6"),
    (r"\[?\[capital pi\]\]?", "\u03a0"),
    (r"\[?\[capital psi\]\]?", "\u03a8"),
    (r"\[?\[capital sigma\]\]?", "\u03a3"),
    (r"\[?\[caret\]\]?", "^"),
    (r"\[?\[congruent with\]\]?", "\u2245"),
    (r"\[?\[curly or open phi\]\]?", "\u03d5"),
    (r"\[?\[dagger\]\]?", "\u2020"),
    (r"\[?\[dbl greater-than\]\]?", "\u226b"),
    (r"\[?\[dbl vertical bar\]\]?", "\u2016"),
    (r"\[?\[degree\]\]?", "\xb0"),
    (r"\[?\[double bond, length as m-dash\]\]?", "="),
    (r"\[?\[double bond, length half m-dash\]\]?", "="),
    (r"\[?\[double dagger\]\]?", "\u2021"),
    (r"\[?\[double equals\]\]?", "\u2267"),
    (r"\[?\[double less-than\]\]?", "\u226a"),
    (r"\[?\[double prime\]\]?", "\u2033"),
    (r"\[?\[downward arrow\]\]?", "\u2193"),
    (r"\[?\[fraction five-over-two\]\]?", "5/2"),
    (r"\[?\[fraction three-over-two\]\]?", "3/2"),
    (r"\[?\[gamma\]\]?", "\u03b3"),
    (r"\[?\[greater-than-or-equal\]\]?", "\u2265"),
    (r"\[?\[greater, similar\]\]?", "\u2273"),
    (r"\[?\[gt-or-equal\]\]?", "\u2265"),
    (r"\[?\[i without dot\]\]?", "\u0131"),
    (r"\[?\[identical with\]\]?", "\u2261"),
    (r"\[?\[infinity\]\]?", "\u221e"),
    (r"\[?\[intersection\]\]?", "\u2229"),
    (r"\[?\[iota\]\]?", "\u03b9"),
    (r"\[?\[is proportional to\]\]?", "\u221d"),
    (r"\[?\[leftrightarrow\]\]?", "\u2194"),
    (r"\[?\[leftrightarrows\]\]?", "\u21c4"),
    (r"\[?\[less-than-or-equal\]\]?", "\u2264"),
    (r"\[?\[less, similar\]\]?", "\u2272"),
    (r"\[?\[logical and\]\]?", "\u2227"),
    (r"\[?\[middle dot\]\]?", "\xb7"),
    (r"\[?\[not equal\]\]?", "\u2260"),
    (r"\[?\[parallel\]\]?", "\u2225"),
    (r"\[?\[per thousand\]\]?", "\u2030"),
    (r"\[?\[prime or minute\]\]?", "\u2032"),
    (r"\[?\[quadruple bond, length as m-dash\]\]?", "\u2263"),
    (r"\[?\[radical dot\]\]?", " \u0307"),
    (r"\[?\[ratio\]\]?", "\u2236"),
    (r"\[?\[registered sign\]\]?", "\xae"),
    (r"\[?\[reverse similar\]\]?", "\u223d"),
    (r"\[?\[right left arrows\]\]?", "\u21c4"),
    (r"\[?\[right left harpoons\]\]?", "\u21cc"),
    (r"\[?\[rightward arrow\]\]?", "\u2192"),
    (r"\[?\[round bullet, filled\]\]?", "\u2022"),
    (r"\[?\[sigma\]\]?", "\u03c3"),
    (r"\[?\[similar\]\]?", "\u223c"),
    (r"\[?\[small alpha\]\]?", "\u03b1"),
    (r"\[?\[small beta\]\]?", "\u03b2"),
    (r"\[?\[small chi\]\]?", "\u03c7"),
    (r"\[?\[small delta\]\]?", "\u03b4"),
    (r"\[?\[small eta\]\]?", "\u03b7"),
    (r"\[?\[small gamma, Greek, dot above\]\]?", "\u03b3\u0307"),
    (r"\[?\[small kappa\]\]?", "\u03ba"),
    (r"\[?\[small lambda\]\]?", "\u03bb"),
    (r"\[?\[small micro\]\]?", "\xb5"),
    (r"\[?\[small mu \]\]?", "\u03bc"),
    (r"\[?\[small nu\]\]?", "\u03bd"),
    (r"\[?\[small omega\]\]?", "\u03c9"),
    (r"\[?\[small phi\]\]?", "\u03c6"),
    (r"\[?\[small pi\]\]?", "\u03c0"),
    (r"\[?\[small psi\]\]?", "\u03c8"),
    (r"\[?\[small tau\]\]?", "\u03c4"),
    (r"\[?\[small theta\]\]?", "\u03b8"),
    (r"\[?\[small upsilon\]\]?", "\u03c5"),
    (r"\[?\[small xi\]\]?", "\u03be"),
    (r"\[?\[small zeta\]\]?", "\u03b6"),
    (r"\[?\[space\]\]?", " "),
    (r"\[?\[square\]\]?", "\u25a1"),
    (r"\[?\[subset or is implied by\]\]?", "\u2282"),
    (r"\[?\[summation operator\]\]?", "\u2211"),
    (r"\[?\[times\]\]?", "\xd7"),
    (r"\[?\[trade mark sign\]\]?", "\u2122"),
    (r"\[?\[triple bond, length as m-dash\]\]?", "\u2261"),
    (r"\[?\[triple bond, length half m-dash\]\]?", "\u2261"),
    (r"\[?\[triple prime\]\]?", "\u2034"),
    (r"\[?\[upper bond 1 end\]\]?", ""),
    (r"\[?\[upper bond 1 start\]\]?", ""),
    (r"\[?\[upward arrow\]\]?", "\u2191"),
    (r"\[?\[varepsilon\]\]?", "\u03b5"),
    (r"\[?\[x with combining tilde\]\]?", "X\u0303"),
]

#: Substitutor that replaces ACS escape codes with the actual unicode character
elsevier_substitute = Substitutor(CHAR_REPLACEMENTS)


class ElsevierSearchDocument(Entity):
    """Document information from Elsevier API search results."""

    test = StringField(".", xpath=True)


class ElsevierSearchScraper(UrlScraper):
    """Scraper for Elsevier search results."""

    entity = ElsevierSearchDocument

    def make_request(self, url):
        driver = webdriver.Firefox()
        driver.get(url)
        sleep(10)
        response = driver.page_source
        driver.quit()
        return response

    def run(self, url):
        """Request URL, scrape response and return an EntityList."""
        if not url:
            return
        response = self.make_request(url)
        selector = Selector.from_html_text(response)
        entities = []
        for root in self.get_roots(selector):
            entity = self.entity(root)
            entity = self.process_entity(entity)
            if entity:
                entities.append(entity)
        return EntityList(*entities)


class ElsevierImage(Entity):
    """Embedded figure. Includes both Schemes and Figures."""

    caption = StringField('dd[id^="labelCaption"]')
    image_url = StringField('a[class="S_C_full_size"]::attr("data-src")')
    process_caption = Chain(elsevier_substitute, normalize)
    process_image_url = LAdd("http://sciencedirect.com")


class ElsevierTableData(Entity):
    """Embedded row data from document tables"""

    rows = StringField("td", all=True)


class ElsevierTable(Entity):
    """Table within document."""

    title = StringField('span[class="label"]')
    column_headings = StringField("th", all=True)
    data = EntityField(ElsevierTableData, "tbody", all=True)
    caption = StringField('div[class="caption"]', all=True)
    process_title = Chain(elsevier_substitute, normalize)
    process_title = Chain(elsevier_substitute, normalize)


class ElsevierHtmlDocument(DocumentEntity):
    """Scraper of document information from Elsevier html papers"""

    doi = StringField(
        'substring-before(substring-after(//script[contains(.,"SDM.doi")]/text(), "SDM.doi = "), ";")',
        xpath=True,
    )
    title = StringField("//title", xpath=True)
    authors = StringField('//ul[@class="authorGroup noCollab svAuthor"]', xpath=True)
    abstract = StringField('//div[@class="abstract svAbstract "]/p', xpath=True)
    journal = StringField('//div[@class="title"]/a', xpath=True)
    volume = StringField('//p[@class="volIssue"]', xpath=True)
    copyright = StringField('//p[@class="copyright"]', xpath=True)
    headings = StringField("//h2[@id]", xpath=True, all=True)
    sub_headings = StringField('//h3[@class="svArticle"]', xpath=True, all=True)
    html_url = UrlField('//meta[@name="dc.identifier"]/@content', xpath=True)
    paragraphs = StringField(
        '//p[@class="svArticle section clear"]', xpath=True, all=True
    )
    figures = EntityField(ElsevierImage, 'dl[class="figure"]', all=True)
    published_date = StringField('//dl[@class="articleDates smh"]', xpath=True)
    citations = StringField('//ul[@class="reference"]', xpath=True, all=True)
    tables = EntityField(ElsevierTable, 'dl[class="table "]', all=True)


class ElsevierHtmlScraper(UrlScraper):
    """Scraper for Elsever html paper pages"""

    entity = ElsevierHtmlDocument


class ElsevierXmlImage(Entity):
    caption = StringField("simple-para")
    label = StringField("label")


class ElsevierXmlTableData(Entity):
    rows = StringField("entry", all=True)


class ElsevierXmlTable(Entity):
    label = StringField("label")
    caption = StringField("caption")
    column_headings = EntityField(ElsevierXmlTableData, "thead row", all=True)
    data = EntityField(ElsevierXmlTableData, "tbody row", all=True)


class ElsevierXmlDocument(Entity):
    """Scraper for Elsevier XML articles"""

    doi = StringField("doi")
    title = StringField("title")
    authors = StringField("creator", all=True)
    abstract = StringField("abstract, ce|abstract-sec, ce|abstract")
    journal = StringField("publicationName")
    volume = StringField("volume")
    issue = StringField("issn")
    pages = StringField("pageRange")
    firstpage = StringField("startingPage")
    lastpage = StringField("endingPage")
    copyright = StringField("copyright")
    publisher = StringField("publisher")
    headings = StringField("section-title", all=True)
    url = UrlField("url")
    paragraphs = StringField("para", all=True)
    figures = EntityField(ElsevierXmlImage, "figure", all=True)
    published_date = StringField("coverDate")
    citations = StringField("bib-reference", all=True)
    tables = EntityField(ElsevierXmlTable, "table", all=True)

    process_abstract = Chain(LStrip(), RStrip(), LStrip("Abstract"))
