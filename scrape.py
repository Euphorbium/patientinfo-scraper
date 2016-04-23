# -*- coding: utf-8 -*-
import unicodecsv
from lxml import html
from retrying import retry
import re, string, random

def scrape_replies(page, top, OP, last_reply=0):
    replies = page.xpath('//div[contains(@class, "post-content")]')[1:]
    lasts = {OP:top+"_top"}
    if replies:
        for ind, reply in enumerate(replies):
            date = reply.xpath('../span/time')[0].attrib["datetime"]
            if len(reply.xpath('../span/a/text()')) > 1:
                to = reply.xpath('../span/a/text()')[1]
            else: to = OP
            poster = reply.xpath('../span/a/text()')[0]
            inferred  = lasts[to]
            lasts[poster] = top+"_"+str(ind+last_reply)
            yield ind, "\n".join(r for r in reply.xpath('./p/text()')), poster, to, inferred, date


@retry(wait_random_min=5000, wait_random_max=10000)
def scrape_thread(thread):
    qid = re.findall(r'\d*$', thread.attrib['href'])[0]
    print base+thread.attrib['href']
    t = html.parse(base+thread.attrib['href'])
    title = thread.text
    for br in t.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    local_id = -1
    unique_id = qid+'_top'
    poster = t.xpath('//div[@id="topic"]/div/a/p/strong')[-1].text
    date = t.xpath('//*[@id="topic"]/article/span/time')[0].attrib['datetime']
    content = '\n'.join(t.xpath('//*[@id="topic"]/article/div[1]/p/text()'))
    row = [unique_id, qid, local_id, title, poster, date, " ", content, " ", subforum]
    w.writerow(row)
    f.flush()
    pages = t.xpath('//select[@name="page"]/option')
    pages = int(pages[-1].attrib["value"]) if pages else 0
    for local_id, reply, username, reply_to, inferred, date in scrape_replies(t, qid, poster):
        row = [qid+"_"+str(local_id), qid, local_id, title, username, date, reply_to, reply, inferred, subforum ]
        w.writerow(row)
    if pages:
        last = local_id
        for p in xrange(1, pages):
            for local_id, reply, username, reply_to, inferred, date in \
                    scrape_replies(html.parse(base+thread.attrib['href']+"?page="+str(p)), unique_id, poster, last):
                row = [qid + "_" + str(local_id), qid, local_id, title, username, date, reply_to, reply, inferred, subforum]
                w.writerow(row)
            last += local_id
    f.flush()

@retry(wait_random_min=5000, wait_random_max=10000)
def parse_page(url):
    print url
    token = str(random.randint(100000, 999999))
    cat_page = html.parse(base+url)
    pages = cat_page.xpath('//select[@name="page"]/option')
    pages = int(pages[-1].attrib["value"]) if pages else 0
    for thread in cat_page.xpath('//ul[@class="thread-list"]/li//h3/a'):
        scrape_thread(thread)
    for page in xrange(1, pages):
        cat_page = html.parse(base + url + "?p_token=" + token + "&page=" + str(page))
        for thread in cat_page.xpath('//ul[@class="thread-list"]/li//h3/a'):
            scrape_thread(thread)


base = "http://patient.info"
start = html.parse("http://patient.info/forums")
f = open('patient.csv', 'w')
w = unicodecsv.writer(f, encoding='utf-8', lineterminator='\n')
w.writerow(['uniqueID', 'qid', 'localID', 'title', 'poster', 'date', 'replyTo', 'content', 'infered_replies', 'category'],)

for letter in string.lowercase:
    for cat in html.parse(base+"/forums/index-"+letter).xpath('//table[@class="zebra-table"]//a'):
        subforum = cat.text
        parse_page(cat.attrib["href"])