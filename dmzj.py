# -*- coding: utf-8 -*-

import requests
import json
from lxml import etree
from bs4 import BeautifulSoup
import click
import os
import execjs
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Referer': 'http://www.dmzj.com/category'
}


PREIX = 'http://manhua.dmzj.com'
PREFIX = 'http://images.dmzj.com/'

# 輸入漫畫網址
def get_request(url):
    r = requests.get(url, headers=headers)
    temp = {}
    try:
        html = etree.HTML(r.content)
        a_tags = html.xpath('//div[@class="cartoon_online_border"]/ul/li/a')
        # 內容簡介
        text_tag = html.xpath('//div[@class="line_height_content"]/text()')[0]
        item = {'data': [], 'synopsis': text_tag.replace('\n', '').strip()}
        for a_tag in a_tags:
            # 具體的某話
            temp = {'title': a_tag.xpath('./@title')[0],
                    'href': PREIX + a_tag.xpath('./@href')[0]}
            item['data'].append(temp)
        
        num = 0
        # 進入章節網址            
        for num in range(len(a_tags)):
            chapter_url = item['data'][num]['href']
            r_chapter = requests.get(chapter_url, headers = headers)
            html = etree.HTML(r_chapter.content)
            script_content = html.xpath('//script[1]/text()')[0]
            vars = script_content.strip().split('\n')
            parse_str = vars[2].strip()  # 取到eval()
            parse_str = parse_str.replace('function(p,a,c,k,e,d)', 'function fun(p, a, c, k, e, d)')
            parse_str = parse_str.replace('eval(', '')[:-1]  # 去除eval
            fun = """
                    function run(){
                        var result = %s;
                        return result;
                    }
                """ % parse_str  # 構造函式調用產生pages變量結果
            pages = execjs.compile(fun).call('run')
            url_list = []       # 圖片list
            if 'shtml' in r_chapter.request.url:
                datas = pages.split('=')[2][1:-2]  # json數據塊 var pages=pages=[]
                url_list = json.JSONDecoder().decode(datas)  # 解碼json數據
            elif 'html' in r_chapter.request.url:
                datas = pages.split('=')[1][1:-2]  # var pages={}
                url_list = json.JSONDecoder().decode(datas)['page_url'].split('\r\n')
            
            headers['Referer'] = item['data'][num]['href']
            comicName = item['data'][num]['title'].split('-')[0]
            chapterName = item['data'][num]['title'].split('-')[1]
            
            if os.path.exists('./%s' % comicName):
                print('已存在%s，進行下一步' % comicName)
                if os.path.exists('./%s/%s' % (comicName, chapterName)):
                    print('已存在%s，進行下一步' % chapterName)
                else:
                    os.mkdir('./%s/%s' % (comicName, chapterName))
            else:
                os.mkdir('./%s' % comicName)

            num = num + 1

            for index, ul in enumerate(url_list):
                img = requests.get(PREFIX + ul, headers=headers)
                time.sleep(1)  # 等待一些時間，防止請求過快
                # click.echo(PREFIX + ul)
                with open('./%s/%s/%s.jpg' % (comicName, chapterName, index), mode='wb') as fp:
                    fp.write(img.content)
                click.echo('save %s.jpg' % index)
            click.echo('complete!')
                
        with open('./details.json', mode='w', encoding='utf-8') as f:
            # ensure_ascii設置為False，防止中文亂碼
            f.write(json.dumps(item, ensure_ascii=False))
    except Exception as e:
        raise e

# 章節網址
def get_chapter(url):
    chapter_url = url
    r_chapter = requests.get(chapter_url, headers = headers)
    try:
        html = etree.HTML(r_chapter.content)
        script_content = html.xpath('//script[1]/text()')[0]
        vars = script_content.strip().split('\n')
        parse_str = vars[2].strip()  # 取到eval()
        parse_str = parse_str.replace('function(p,a,c,k,e,d)', 'function fun(p, a, c, k, e, d)')
        parse_str = parse_str.replace('eval(', '')[:-1]  # 去除eval
        fun = """
                function run(){
                    var result = %s;
                    return result;
                }
            """ % parse_str  # 構造函式調用產生pages變量結果
        pages = execjs.compile(fun).call('run')
        url_list = []       # 圖片list
        if 'shtml' in r_chapter.request.url:
            datas = pages.split('=')[2][1:-2]  # json數據塊 var pages=pages=[]
            url_list = json.JSONDecoder().decode(datas)  # 解碼json數據
        elif 'html' in r_chapter.request.url:
            datas = pages.split('=')[1][1:-2]  # var pages={}
            url_list = json.JSONDecoder().decode(datas)['page_url'].split('\r\n')
        
        soup = BeautifulSoup(r_chapter.text, 'lxml')
        comicName = soup.find(class_='redhotl').prettify('utf-8').decode('utf-8').split('\n')[1].split(' ')[1]
        chapterName = soup.find_all(class_='redhotl')[1].prettify('utf-8').decode('utf-8').split('\n')[1].split(' ')[1]
        
        
        if not os.path.exists('./%s' % comicName):
            os.mkdir('./%s' % comicName)
            print('\n創建 "%s" 資料夾' % comicName)
            
            if not os.path.exists('./%s/%s' % (comicName, chapterName)):
                os.mkdir('./%s/%s' % (comicName, chapterName))
                print('創建 "%s" 資料夾\n' % chapterName)
            else:
                print('已存在 "%s"，進行下一步\n' % chapterName)
        else:
            print('已存在 "%s"，直接進行下一步\n' % comicName)
        

        for index, ul in enumerate(url_list):
            img = requests.get(PREFIX + ul, headers=headers)
            time.sleep(1)  # 等待一些時間，防止請求過快
            # click.echo(PREFIX + ul)
            with open('./%s/%s/%s.jpg' % (comicName, chapterName, index), mode='wb') as fp:
                fp.write(img.content)
            click.echo('save %s.jpg' % index)
        click.echo('\n%s complete!\n' % chapterName)
    except Exception as e:
        raise e
    

        
if __name__ == '__main__':
    
    print('動漫之家漫畫下載\n作者：rtshaw\n')
    print('模式 1→若要下載所有話數，直接輸入漫畫網址，例如：https://manhua.dmzj.com/wohesaozidetongjushenghuo\n模式 2→若只需要下載單話，輸入章節網址，例如：https://manhua.dmzj.com/wohesaozidetongjushenghuo/55694.shtml#@page=1\n')
    model = int(input('請選擇模式：'))
    print('你選擇了模式 %d' % model)
    
    if model == 1:
        get_request(str(input('\n請輸入漫畫網址：')))
        print('\n所有任務已完成')
        input('按任意鍵退出')
    elif model == 2:
        get_chapter(str(input('\n請輸入章節網址：')))
        print('\n所有任務已完成')
        input('按任意鍵退出')
