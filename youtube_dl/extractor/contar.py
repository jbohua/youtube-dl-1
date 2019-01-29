# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    urlencode_postdata,
    compat_str,
    ExtractorError,
)

class ContarBaseIE(InfoExtractor):
    
    _NETRC_MACHINE = 'contar'
    _API_BASE = 'https://api.cont.ar/api/v2/'

    def _handle_errors(self, result):
        error = result.get('error', {}).get('message')
        if error:
            if isinstance(error, dict):
                error = ', '.join(error.values())
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, error), expected=True)

    def _call_api(self, path, video_id, headers = {}):
        if self._auth_token:
            headers['Authorization'] = 'Bearer ' + self._auth_token
        
        result = self._download_json(
            self._API_BASE + path, video_id, headers=headers)
        
        self._handle_errors(result)
        return result['data']
        
    def _real_initialize(self):
        email, password = self._get_login_info()
        if email is None:
            self.raise_login_required()

        result = self._download_json(
            self._API_BASE + 'authenticate', None, data=urlencode_postdata({
                'email': email,
                'password': password,
            }))
        
        self._handle_errors(result)
        self._auth_token = result['token']
        
    def _get_video_info(self, video, video_id):
        #print(json.dumps(video, indent=4, sort_keys=True))
        #print "id = %s S%sE%s" % (video.get('id'), season.get('name') , video.get('episode'))
        episode_number = int_or_none(video.get('episode'))
        
        formats = self._get_formats(video.get('streams', []), video.get('id'))
        subtitles = self._get_subtitles(video['subtitles'].get('data', []), video.get('id'))
        
        info = {
            'id': video.get('id'),
            'title': video.get('name'),
            'description': video.get('synopsis'),
            'series': video.get('serie_name'),
            'episode': video.get('name'),
            'episode_number': int_or_none(video.get('episode')),
            'season_number': int_or_none(video.get('serie')),
            'season_id': video.get('season'),
            'episode_id': video.get('id'),
            'duration': int_or_none(video.get('length')),
            'thumbnail': video.get('posterImage'),
            #'timestamp': timestamp,
            'formats': formats,
            'subtitles': subtitles,
        }
        
        return info
    
    def _get_subtitles(self, subtitles, video_id):
        subs = {}
        for sub in subtitles:
            lang = sub.get('lang').lower()
            subs[lang] = [{ 'url': sub.get('url'), 'ext': 'srt'}]
        
        return subs
    
    def _get_formats(self, videos, video_id):
        formats = []
        for stream in videos:
            stream_url = stream.get('url')
            type = stream.get('type')
            if (type == 'HLS'):
                formats.extend(self._extract_m3u8_formats(stream_url,
                video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls',
                fatal=False))
            elif (type == 'DASH'):
                formats.extend(self._extract_mpd_formats(
                    stream_url, video_id, mpd_id='dash', fatal=False))
        
        self._sort_formats(formats)
        return formats
    
    
class ContarIE(ContarBaseIE):
    
    _UUID_RE = r'[\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12}'
    _VALID_URL = r'https?://(?:www\.)?cont\.ar/watch/(?P<id>%s)' % _UUID_RE
    _TEST = {
        'url': 'https://www.cont.ar/watch/d2815f05-f52f-499f-90d0-5671e9e71ce8',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': 'd2815f05-f52f-499f-90d0-5671e9e71ce8',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }
            
    def _real_extract(self, url):
        video_id = self._match_id(url)
        
        video = self._call_api('videos/' + video_id, video_id, headers={'Referer': url})
        info = self._get_video_info(video, video_id);
        return info
        
        
class ContarSerieIE(ContarBaseIE):
    
    _UUID_RE = r'[\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12}'
    _VALID_URL = r'https?://(?:www\.)?cont\.ar/serie/(?P<id>%s)' % _UUID_RE
    _TEST = {
        'url': 'https://www.cont.ar/serie/353247d5-da97-4cb6-8571-c4fbab28c643',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': 'd2815f05-f52f-499f-90d0-5671e9e71ce8',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }
        
    def _real_extract(self, url):
        video_id = self._match_id(url)
        
        video = self._call_api('serie/' + video_id, video_id, headers={'Referer': url})
        import json
        
        seasons = []
        entries = []
        for season in video['seasons'].get('data', []):
            #print(json.dumps(season, indent=4, sort_keys=True))
            season_number = season.get('name')
            for episode in season['videos'].get('data', []):
                info = self._get_video_info(video, video_id);
                entries.append(info)
        
        return self.playlist_result(
            entries, video_id,
            video.get('title'), video.get('synopsis'))  
        

class ContarChannelIE(ContarBaseIE):
    
    _UUID_RE = r'[\d]{1,}'
    _VALID_URL = r'https?://(?:www\.)?cont\.ar/channel/(?P<id>%s)' % _UUID_RE
    _TEST = {
        'url': 'https://www.cont.ar/channel/242',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '242',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }
    
    def _real_extract(self, url):
        list_id = self._match_id(url)
        
        list = self._call_api('channel/series/' + list_id, list_id, headers={'Referer': url})
        entries = [] 
        
        for video in list:
            if (video.get('type') == 'SERIE'):
                url = 'www.cont.ar/serie/%s' % video.get('uuid')
                entries.append(self.url_result(url, video_id=video.get('uuid'), video_title=video.get('name')))
        
        return self.playlist_result(
            entries, list_id)  

class ContarBrowseIE(ContarBaseIE):
    
    _UUID_RE = r'[\d]{1,}'
    _VALID_URL = r'https?://(?:www\.)?cont\.ar/browse/genre/(?P<id>%s)' % _UUID_RE
    _TEST = {
        'url': 'https://www.cont.ar/browse/genre/46',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '46',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }
        
    def _real_extract(self, url):
        list_id = self._match_id(url)
        
        list = self._call_api('full/section/' + list_id, list_id, headers={'Referer': url})
        entries = [] 
        
        for video in list['videos'].get('data', []):
            if (video.get('type') == 'SERIE'):
                url = 'www.cont.ar/serie/%s' % video.get('uuid')
                entries.append(self.url_result(url, video_id=video.get('uuid'), video_title=video.get('name')))
        
        return self.playlist_result(
            entries, list_id,
            list.get('title'))  
        
