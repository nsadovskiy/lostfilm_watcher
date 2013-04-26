#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from os import listdir
from os.path import join, isfile
from urllib2 import urlopen, Request


conf_file_name = u'lostfilm.conf'
rss_url = 'http://www.lostfilm.tv/rssdd.xml'
rss_encoding = '1251'

link_re = re.compile('<link>(.+)</link>')
hd_re = re.compile('(720[pP])|(1080[pP])|(\.[hH][dD]\.)')
web_re = re.compile('\.[Ww][Ee][Bb]\.')
filename_re = re.compile('id=.+;(.+)')


def load_settings(file_name):
    result = {
            'uid':         None,
            'pass':        None,
            'usess':       None,
            'target_path': None,
            'torrents':    [],
            'cookies':     None
        }
    with open(file_name) as f:
        for line in [l for l in [l.strip() for l in f] if l and not l[0] == '#']:
            options = [
                    option.strip().lower() if index == 0 else option.strip()
                    for index, option in enumerate(line.split())
                ]
            if options[0] == 'torrent' and len(options) > 1:
                torrent = [options[1], None, None]
                for o in [ o.lower() for o in options[2:]]:
                    if o == 'hd':
                        torrent[1] = True
                    elif o == 'sd':
                        torrent[1] = False
                    elif o == 'web':
                        torrent[2] = True
                    elif o == 'noweb':
                        torrent[2] = False
                    else:
                        print u'[WARNING] Unknown torrent option "%s"' % o
                result['torrents'].append(torrent)
            elif options[0] in result and len(options) > 1:
                result[options[0]] = options[1]
            else:
                print u'[WARNING] Unknown option "%s"' % option[0]
    result['cookies'] = 'uid=%s; pass=%s; usess=%s' % (
            result['uid'],
            result['pass'],
            result['usess']
        )
    return result


def load_links(url, cookies):
    print 'Reading RSS ...'
    response = urlopen(Request(url, None, {'Cookie': cookies}))
    response = response.read().decode(rss_encoding)
    # print response
    return [{
                'url': unicode(item),
                'is_hd': bool(hd_re.search(item)),
                'is_web': bool(web_re.search(item))
            } for item in link_re.findall(response)
        ]

def file_exists(file_name, path):
    for f in listdir(path):
        # print f, file_name, f.find(file_name)
        if f.find(file_name) >= 0:
            return True
    return False

def download_torrent(url, cookies, path):
    file_name = filename_re.search(url).group(1)
    full_path = join(path, file_name)
    if not file_exists(file_name, path):
        print '... downloading "%s" ...' % file_name
        response = urlopen(Request(url, None, {'Cookie': cookies}))
        open(full_path, 'wb').write(response.read())

if __name__ == '__main__':
    settings = load_settings(conf_file_name)
    links = load_links(rss_url, settings['cookies'])
    for movie in settings['torrents']:
        for link in links:
            try:
                if re.search(movie[0], link['url']):
                    if link['is_hd'] == movie[1] or movie[1] is None:
                        if link['is_web'] == movie[2] or movie[2] is None:
                            download_torrent(link['url'], settings['cookies'], settings['target_path'])
            except Exception as e:
                print '[ERROR] ', unicode(e)
