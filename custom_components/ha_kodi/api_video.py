
import aiohttp, xmltodict, os, hashlib, m3u8
from urllib.parse import urlparse
import urllib.request 

class Video():

    def __init__(self, hass, data_dir, api_url):
        self.hass = hass
        self.data_dir = data_dir
        self.api_url = api_url

    # 调用服务
    def call_service(self, domain, service, data):
        self.hass.async_create_task(self.hass.services.async_call(domain, service, data))

    def notify(self, msg):
        self.call_service('persistent_notification', 'create', {
            'message': msg,
            'title': 'Kodi视频通知',
            'notification_id': 'api_video'
        })

    # 播放视频
    async def play_video(self, call):
        data = call.data
        _name = data['name']
        entity_id = data['entity_id']
        _dict = await self.get_series(_name)
        if isinstance(_dict, dict):
            # 生成文件
            self.call_service('media_player', 'play_media', {
                'entity_id': entity_id,
                'media_content_type': 'playlist',
                'media_content_id': _dict['video_url']
            })
            self.notify("开始播放视频【" + _dict['name'] + "】，请检查是否已经播放")
    
    # 获取视频剧集
    async def get_series(self, keywords):
        async with aiohttp.ClientSession() as session:
            url = 'https://api.shijiapi.com/api.php/provide/vod/at/xml/?wd=' + keywords
            print(url)
            async with session.get(url) as res:
                xml_result = await res.text()
                json_result = xmltodict.parse(xml_result, encoding='utf-8')
                #print(json_result)
                video = json_result['rss']['list']['video']
                if video:
                    if isinstance(video, list):
                        video = video[0]
                    id = str(video['id'])
                    url = 'https://api.shijiapi.com/api.php/provide/vod/at/xml/?ac=videolist&ids=' + id
                    print(url)
                    async with session.get(url) as res:
                        xml_result = await res.text()
                        json_result = xmltodict.parse(xml_result, encoding='utf-8')
                        #print(json_result)
                        dd = json_result['rss']['list']['video']['dl']['dd']
                        # print(dd)
                        _dd = list(filter(lambda x: x['@flag'].count('m3u8') > 0, dd))
                        # print(_dd)
                        obj = _dd[0]
                        arr = obj['#text'].split('#')
                        # 生成文件                        
                        file_content = '#EXTM3U'
                        _list = []
                        for item in arr:
                            _arr = item.split('$')
                            if len(_arr) == 2:
                                _title = video['name'] + '-' + _arr[0]
                                _url = _arr[1]
                                file_content += '\n#EXTINF:-1, ' + _title + '\n' + _url
                                _list.append({'title': _title, 'url': _url})
                        # 写入文件
                        file_path = '{0}{1}.m3u'.format(self.data_dir, id)
                        self.save_file(file_path, file_content)
                        video_url =  '{0}data/{1}.m3u'.format(self.api_url, id)
                        print('播放链接：', video_url)
                        return {'id':id, 'name': video['name'], 'list': _list, 'video_url': video_url}
        return None
    
    # 查看原始链接
    async def get_download_list(self, url):
        file_dir = self.md5(url)
        dir = self.data_dir + file_dir
        self.mkdir(dir)
        parsed_uri = urlparse(url)
        host = '{probuf.scheme}://{host.netloc}'.format(probuf=parsed_uri, host=parsed_uri)
        print('基础链接：', host)
        print('当前下载链接：', url)
        # 开始下载
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                file_buffer = await res.text()
        variant_m3u8 = m3u8.loads(file_buffer)
        if variant_m3u8.is_variant:
            for playlist in variant_m3u8.playlists:
                absolute_url = host + playlist.uri
                # 获取相对路径
                relative_path = playlist.uri.replace('index.m3u8', '')
                print(relative_path)
                # 下载index.m3u8文件
                print('开始下载，真实m3u8地址：', absolute_url)
                index_path = '{0}/index.m3u8'.format(dir)
                # 开始下载
                async with aiohttp.ClientSession() as session:
                    async with session.get(absolute_url) as res:
                        file_buffer = await res.text()
                    
                    self.save_file(index_path, file_buffer)

                # urllib.request.urlretrieve(absolute_url, index_path)
                
                # 加载index.m3u8
                playlist = m3u8.loads(file_buffer)
                index_m3u8_url = '{0}data/{1}/index.m3u8'.format(self.api_url, file_dir)
                print(index_m3u8_url)
                _list = [index_m3u8_url]
                for seg in playlist.segments:
                    # print(host + seg.uri)
                    _list.append(host + seg.uri)
                # 写入文件
                #list_path = '{0}/list.txt'.format(dir)
                #with open(list_path, 'w', encoding='utf-8') as f:
                #   f.write('\n'.join(_list))
                # 重新保存index文件
                with open(index_path, "r", encoding='utf-8') as f:
                    content = f.read()
                with open(index_path, "w", encoding='utf-8') as f:
                    f.write(content.replace(relative_path, ''))
                return _list

    def md5(self, text):
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    # 创建文件夹
    def mkdir(self, path):
        folders = []        
        while not os.path.isdir(path):
            path, suffix = os.path.split(path)
            folders.append(suffix)
        for folder in folders[::-1]:
            path = os.path.join(path, folder)
            os.mkdir(path)
    # 保存文件
    def save_file(self, file_path, file_content):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)