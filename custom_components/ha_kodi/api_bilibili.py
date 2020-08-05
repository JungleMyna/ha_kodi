'''

console.log("%c==============复制以下内容==============", "color:red"); 
let tmp = []
document.cookie.split('; ').forEach(ele=>{ 
    let arr=ele.split('=');
    tmp.push(`"${arr[0].trim()}": "${arr[1].trim()}"`)
});
console.log(tmp.join('\n')) 
console.log("%c==============复制以上内容==============","color:red");

'''
import aiohttp, json, os

class Bilibili():

    def __init__(self, hass):
        # 读取cookie
        self.hass = hass        
        self.headers = {
            'Host': 'api.bilibili.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        }
        self.cookie = {}
        self.read_cookie()

    async def get(self, url):
        # 请求地址
        result = None
        jar = aiohttp.CookieJar(unsafe=True)
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookie, cookie_jar=jar) as session:
            async with session.get(url) as resp:
                result = await resp.json()
        return result

    def read_cookie(self):
        # 读取cookie
        try:
            filename = self.hass.config.path(".storage") + '/bilibili_cookie.json'
            if os.path.isfile(filename):
                with open(filename) as file_obj:
                    self.cookie = json.load(file_obj)
                    print("读取cookie成功", self.cookie)
        except Exception as ex:
            print(ex)

    def notify(self, msg):
        self.hass.services.call('persistent_notification', 'create', {
            'message': msg,
            'title': '哔哩哔哩接口通知',
            'notification_id': 'api_bilibili'
        })

    def set_cookie(self, call):
        # 设置cookie
        cookie = {}
        data = call.data
        for key,values in data.items():
            cookie[key] = values
        print("设置cookie成功", json.dumps(cookie))
        self.cookie = cookie
        # 保存cookie到本地
        filename = self.hass.config.path(".storage") + '/bilibili_cookie.json'
        with open(filename,'w', encoding='utf-8') as file_obj:
           json.dump(cookie, file_obj, ensure_ascii=False)
           self.notify('保存cookie成功')
            

    async def search(self, keyword):
        # 搜索
        url = 'https://api.bilibili.com/x/web-interface/search/all/v2?keyword=' + keyword
        print(url)
        res = await self.get(url)        
        media_bangumi = res['data']['result'][3]['data'][0]
        # print(media_bangumi)
        _list = []
        for item in media_bangumi['eps']:
            _list.append({
                'id': item['id'],
                'cover': item['cover'],
                'title': '{0}.{1}'.format(item['index_title'], item['long_title']),
                'url': item['url']
            })

        return {
            'title': media_bangumi['title'].replace('<em class="keyword">', "").replace('</em>', ''),
            'url': media_bangumi['url'],
            'cover': media_bangumi['cover'],
            'type': media_bangumi['type'],
            'list': _list
        }
        media_bangumi['data'][0]

    async def get_bangumi_video(self, ep_id):
        # 获取番剧视频地址
        url = 'https://api.bilibili.com/pgc/player/web/playurl/html5?ep_id=' + str(ep_id)
        print(url)
        res = await self.get(url)
        result = res['result']
        item = result['durl'][0]
        return {
            'url': item['url'],
            'length': item['length'],
            'size': item['size'],
            'type': result['type']
        }