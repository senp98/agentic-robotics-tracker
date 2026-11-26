#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 data/ 和 notes/ 合成页面读取的 docs/data.js。

    python3 scripts/build.py
"""
import tracker

if __name__ == '__main__':
    size = tracker.build()
    data = tracker.build_data()
    items = data['items']
    print('写入 docs/data.js：%d 条（%d 篇论文，%d 篇博客），%d KB，数据日期 %s' % (
        len(items), sum(1 for x in items if x['k'] == 'p'), sum(1 for x in items if x['k'] == 'b'),
        size // 1024, data['asof']))
