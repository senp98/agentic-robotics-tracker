#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拉取新论文、回溯引用、刷新被引数和 stars。只用标准库。

    python3 scripts/update.py                  例行更新（GitHub Actions 每周跑这一条）
    python3 scripts/update.py --dry-run        只打印会做什么，不写文件
    python3 scripts/update.py --add 2611.12345 [更多编号]     手工加论文
    python3 scripts/update.py --add-blog URL --title 标题 --date 2026-11-30 --author 作者

新条目一律标为未读。判断是否相关用的是关键词规则，会放进不相关的论文；
不想要的编号写进 data/ignore.txt。
"""
import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter

import tracker as T

UA = 'agentic-robotics-tracker (https://github.com/senp98/agentic-robotics-tracker)'
CACHE = os.path.join(T.ROOT, '.cache', 'html')
NS = {'a': 'http://www.w3.org/2005/Atom', 'x': 'http://arxiv.org/schemas/atom'}
DEADLINE = time.time() + 20 * 60  # 整次更新最多 20 分钟，超时后跳过剩下的网络请求

# 相关性规则：标题 + 摘要里既要有机器人词，也要有 agent 词，分类在下面几类之内。
ROBOT = re.compile(r'robot|embodied|manipulat|humanoid|locomot|quadruped|physical (world|ai|agent|intelligence)', re.I)
AGENT = re.compile(
    r'agentic|harness|code[- ]as[- ]polic|coding agent|robot-use|LLM[- ]agent|VLM[- ]agent|self-improv|self-evolv'
    r'|frontier (model|agent|VLM|MLLM)|GPT-\d|Claude|Gemini|tool[- ]call|tool[- ]use|orchestrat|as[- ]policy'
    r'|program synthesis|writes? (code|programs?)', re.I)
OFF_TOPIC = re.compile(
    r'strategic classification|opinion|perimeter defense|wildfire|cryptocurrency|sepsis|inventory|radio network|O-RAN'
    r'|drone-mesh|pathfinding|autonomous driving|UAV swarm|minecraft|video generation|3D (asset|scene) generation'
    r'|talking avatar|surgical|endoscop|patient', re.I)
CATEGORIES = ('cs.RO', 'cs.AI', 'cs.CV', 'cs.CL', 'cs.LG', 'cs.SE', 'cs.HC', 'cs.MA')
VENUE = re.compile(
    r'\b(NeurIPS|ICML|ICLR|CVPR|ICCV|ECCV|CoRL|RSS|ICRA|IROS|AAAI|IJCAI|ACL|EMNLP|NAACL|RA-L|T-RO|IJRR|TMLR|TPAMI'
    r'|Science Robotics|Humanoids|HRI|CASE|RO-MAN|WACV)\b[ ,\']*((?:20)?2[2-9])?')


def log(msg):
    print(msg, flush=True)


def late():
    return time.time() > DEADLINE


def fetch(url, data=None, headers=None, tries=3, wait=5, timeout=60):
    """失败返回 None，不抛异常：某个来源挂了不该让整次更新失败。"""
    h = {'User-Agent': UA}
    h.update(headers or {})
    err = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return None
            err = e
        except Exception as e:  # 网络错误、超时
            err = e
        if k + 1 < tries:
            time.sleep(wait * (k + 1))
    log('  请求失败 %s：%s' % (url.split('?')[0][:70], err))
    return None


# ---------------------------------------------------------------- arXiv
def parse_atom(xml):
    out = []
    for e in ET.fromstring(xml).findall('a:entry', NS):
        aid = (e.findtext('a:id', '', NS) or '').rsplit('/abs/', 1)[-1]
        pc = e.find('x:primary_category', NS)
        text = lambda tag, ns='a': ' '.join((e.findtext('%s:%s' % (ns, tag), '', NS) or '').split())
        if not aid or not text('title'):
            continue
        out.append({
            'id': re.sub(r'v\d+$', '', aid), 'title': text('title'), 'date': text('published')[:10],
            'authors': [a.findtext('a:name', '', NS) for a in e.findall('a:author', NS)],
            'abstract': text('summary'), 'cat': pc.get('term') if pc is not None else '',
            'comment': text('comment', 'x'), 'journal_ref': text('journal_ref', 'x'),
        })
    return out


def arxiv(params):
    xml = fetch('https://export.arxiv.org/api/query?' + urllib.parse.urlencode(params), tries=2, wait=8, timeout=45)
    time.sleep(3.1)  # arXiv 要求请求间隔 3 秒
    try:
        return parse_atom(xml) if xml else None
    except ET.ParseError:
        return None


def arxiv_by_id(ids):
    out = {}
    for k in range(0, len(ids), 40):
        chunk = ids[k:k + 40]
        res = arxiv({'id_list': ','.join(chunk), 'max_results': len(chunk)})
        if res is None or late():
            log('  arXiv 接口没有响应，剩下的 %d 个编号这次不查' % (len(ids) - k))
            break
        for r in res:
            out[r['id']] = r
    return out


def relevant(r):
    txt = r['title'] + ' ' + r['abstract']
    return bool(r['cat'] in CATEGORIES and not OFF_TOPIC.search(txt) and ROBOT.search(txt) and AGENT.search(txt))


def venue_claim(r):
    """从作者在 arXiv 写的备注里取发表去向；投稿中的不算。"""
    txt = ' '.join([r.get('journal_ref', ''), r.get('comment', '')])
    m = VENUE.search(txt)
    if not m:
        return ''
    near = txt[max(0, m.start() - 60): m.end() + 30].lower()
    if re.search(r'submi|under review|in submission', near):
        return ''
    name = m.group(0).strip(" ,'")
    return name + (' (workshop)' if 'workshop' in near else '')


# ---------------------------------------------------------------- 全文、代码仓库
def fulltext(pid):
    """返回 (正文, 参考文献条目, GitHub 链接)；arXiv 没有 HTML 版时返回 None。"""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, pid + '.html')
    if os.path.exists(path):
        with open(path, 'rb') as f:
            raw = f.read()
    else:
        raw = None if late() else fetch('https://arxiv.org/html/' + pid, tries=2, timeout=45)
        time.sleep(1)
        if not raw or len(raw) < 20000:
            return None
        with open(path, 'wb') as f:
            f.write(raw)
    return T.split_fulltext(raw.decode('utf-8', 'ignore'))


def plausible_repo(repo, title):
    """正文里的 GitHub 链接很多是别人的仓库；只认名字和论文标题对得上的。"""
    squash = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
    parts = repo.split('/')
    if len(parts) < 3:
        return False
    owner, name = squash(parts[1]), squash(parts[2])
    head = squash(re.split(r'[:\s]', title.strip())[0])
    words = [squash(w) for w in re.findall(r'[A-Za-z0-9-]{4,}', title)][:6]
    return bool(name) and ((len(head) >= 3 and (head in name or name in head or head in owner)) or any(w and w in name for w in words))


def hf_paper(pid):
    raw = None if late() else fetch('https://huggingface.co/api/papers/' + pid, tries=2, timeout=30)
    time.sleep(0.4)
    try:
        return json.loads(raw) if raw else None
    except ValueError:
        return None


def github_stars(repo):
    if late():
        return None
    slug = '/'.join(repo.split('/')[1:3])
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        raw = fetch('https://api.github.com/repos/' + slug, tries=2, timeout=30,
                    headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'})
        try:
            return json.loads(raw).get('stargazers_count') if raw else None
        except ValueError:
            return None
    raw = fetch('https://github.com/' + slug, tries=2, timeout=30)
    time.sleep(1)
    m = re.search(r'"stargazerCount":\s*(\d+)', raw.decode('utf-8', 'ignore')) if raw else None
    return int(m.group(1)) if m else None


def make_paper(r, lib_titles, refs, today):
    """arXiv 记录 -> papers.jsonl 的一行；顺带把它的参考文献记进 refs。"""
    p = {'id': r['id'], 'type': 'paper', 'title': r['title'], 'date': r['date'], 'authors': r['authors'], 'abstract': r['abstract']}
    if venue_claim(r):
        p['venue'] = venue_claim(r)
    auto = {'topics': T.tag_topics(r['title'], r['abstract']), 'unitree': [], 'benchmarks': [], 'models': []}
    ft = fulltext(r['id'])
    links = []
    if ft:
        body, entries, links = ft
        auto.update(T.tag_fulltext(body))
        if entries:
            refs['refs'][r['id']] = sorted(T.refs_of(entries, lib_titles) - {r['id']})
    hf = hf_paper(r['id']) or {}
    repo = (hf.get('githubRepo') or '').replace('https://', '').replace('http://', '').rstrip('/')
    if not repo:
        repo = next((g for g in links if plausible_repo(g, r['title'])), '')
    if repo:
        p['repo'] = repo
    p['auto'] = auto
    p['fulltext'] = bool(ft)
    p['added'] = today
    return p


# ---------------------------------------------------------------- 三个步骤
def search_new(src, known, today):
    """按 sources.json 里的检索词找最近发布、库里没有的论文。"""
    cutoff = (datetime.date.fromisoformat(today) - datetime.timedelta(days=src.get('lookback_days', 21))).isoformat()
    found, failed = {}, 0
    for q in src.get('arxiv_queries', []):
        res = arxiv({'search_query': q['query'], 'max_results': q.get('max', 100), 'sortBy': 'submittedDate', 'sortOrder': 'descending'})
        if res is None:
            failed += 1
            if failed >= 2:
                log('  arXiv 接口连续没有响应，这次不检索新论文')
                break
            continue
        hit = [r for r in res if r['date'] >= cutoff and r['id'] not in known and relevant(r)]
        for r in hit:
            found.setdefault(r['id'], r)
        log('  检索 %-18s 返回 %3d 条，新的相关论文 %d 篇' % (q['name'], len(res), len(hit)))
    return list(found.values())


def backtrack(src, refs, known):
    """库内论文引用得多、但库里没有的论文。评估过且不相关的记进 skipped，下次不再查。"""
    need = src.get('backtrack_min_citations', 10)
    seen = known | set(refs.get('skipped', []))
    cnt = Counter(i for ids in refs['refs'].values() for i in set(ids) if i not in seen)
    cand = sorted(i for i, n in cnt.items() if n >= need)
    if not cand:
        return []
    meta = arxiv_by_id(cand)
    keep = []
    for i in cand:
        r = meta.get(i)
        if r is None:
            continue  # 没取到元数据，下次再试
        if relevant(r):
            keep.append(r)
            log('  回溯引用：%s 被库内 %d 篇引用 → 加入  %s' % (i, cnt[i], r['title'][:60]))
        else:
            refs.setdefault('skipped', []).append(i)
    return keep


def refresh_venues(papers, today):
    """预印本后来被接收时，作者通常会更新 arXiv 备注。只查近 18 个月、还没有去向的论文。"""
    cutoff = (datetime.date.fromisoformat(today) - datetime.timedelta(days=540)).isoformat()
    todo = [p for p in papers if p['type'] == 'paper' and not p.get('venue') and p['date'] >= cutoff]
    meta = arxiv_by_id([p['id'] for p in todo])
    n = 0
    for p in todo:
        v = venue_claim(meta.get(p['id'], {}))
        if v:
            p['venue'] = v
            n += 1
            log('  发表去向：%s → %s' % (p['id'], v))
    return n


def refresh_signals(papers, sig, refs, today, only=None):
    """only 给出编号集合时，只为这几篇查外部数字（手工加论文时用）；库内被引总是全部重算。"""
    rows = sig['papers']
    ids = [p['id'] for p in papers if p['type'] == 'paper']
    for i in ids:
        rows.setdefault(i, {})
    want = [i for i in ids if only is None or i in only]
    # 库内被引：直接从 refs 数
    cnt = Counter(i for src, cited in refs['refs'].items() for i in set(cited) if i != src)
    for i in ids:
        rows[i]['cited_in_library'] = cnt.get(i, 0)
    # Semantic Scholar：批量接口，一次最多 500 个编号
    ok = 0
    for k in range(0, len(want), 400):
        chunk = want[k:k + 400]
        raw = fetch('https://api.semanticscholar.org/graph/v1/paper/batch?fields=citationCount,influentialCitationCount',
                    data=json.dumps({'ids': ['ARXIV:' + i for i in chunk]}).encode(),
                    headers={'Content-Type': 'application/json'}, tries=3, wait=20, timeout=60)
        try:
            res = json.loads(raw) if raw else None
        except ValueError:
            res = None
        if not (isinstance(res, list) and len(res) == len(chunk)):
            log('  Semantic Scholar 没有返回结果，这 %d 篇保留上次的数字' % len(chunk))
            continue
        for i, r in zip(chunk, res):
            if r and r.get('citationCount') is not None:
                rows[i]['s2'] = r['citationCount']
                rows[i]['s2_influential'] = r.get('influentialCitationCount') or 0
                ok += 1
        time.sleep(2)
    log('  Semantic Scholar：更新 %d 篇' % ok)
    # 近 60 天、还没有代码仓库的论文：问 Hugging Face 有没有登记仓库
    cutoff = (datetime.date.fromisoformat(today) - datetime.timedelta(days=60)).isoformat()
    found = 0
    for p in papers:
        if p['type'] == 'paper' and not p.get('repo') and p['date'] >= cutoff and only is None:
            hf = hf_paper(p['id'])
            if hf:
                if isinstance(hf.get('upvotes'), int):
                    rows[p['id']]['hf_upvotes'] = hf['upvotes']
                if hf.get('githubRepo'):
                    p['repo'] = hf['githubRepo'].replace('https://', '').replace('http://', '').rstrip('/')
                    found += 1
    log('  Hugging Face：新登记的代码仓库 %d 个' % found)
    # GitHub stars
    got = miss = 0
    for p in papers:
        if p.get('repo', '').startswith('github.com/') and (only is None or p['id'] in only):
            n = github_stars(p['repo'])
            if n is None:
                miss += 1
            else:
                rows[p['id']]['stars'] = n
                got += 1
    log('  GitHub stars：更新 %d 个仓库，%d 个没取到（保留上次的数字）' % (got, miss))
    for i in list(rows):
        if i not in ids:
            del rows[i]
    return ok > 0 or got > 0


def blog_id(url):
    u = urllib.parse.urlparse(url)
    host = [h for h in u.netloc.lower().split('.') if h not in ('www', 'com', 'org', 'io', 'ai', 'net', 'edu', 'github', 'substack', 'medium')]
    last = [s for s in u.path.split('/') if s]
    slug = '%s-%s' % (host[-1] if host else 'blog', os.path.splitext(last[-1])[0] if last else 'post')
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', slug.lower())).strip('-')[:70]


def main():
    ap = argparse.ArgumentParser(description='拉取新论文、回溯引用、刷新数字')
    ap.add_argument('--dry-run', action='store_true', help='只打印，不写文件')
    ap.add_argument('--add', nargs='+', metavar='编号', help='手工加入指定 arXiv 编号')
    ap.add_argument('--add-blog', metavar='URL', help='手工加入一篇博客')
    ap.add_argument('--title'); ap.add_argument('--date'); ap.add_argument('--author', default='')
    ap.add_argument('--no-search', action='store_true', help='不检索新论文')
    ap.add_argument('--no-signals', action='store_true', help='不刷新被引数和 stars')
    a = ap.parse_args()

    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    src, papers, sig, refs, ignore = T.load_sources(), T.load_papers(), T.load_signals(), T.load_refs(), T.load_ignore()
    known = {p['id'] for p in papers} | ignore
    lib_titles = {p['id']: T.norm(p['title']) for p in papers if p['type'] == 'paper'}
    added = []

    if a.add_blog:
        if not (a.title and a.date and re.match(r'^\d{4}-\d{2}-\d{2}$', a.date)):
            sys.exit('加博客需要 --title 和 --date（格式 2026-11-30）')
        bid = blog_id(a.add_blog)
        if bid in known:
            sys.exit('已经有这一条了：' + bid)
        p = {'id': bid, 'type': 'blog', 'title': a.title, 'date': a.date, 'authors': [a.author or urllib.parse.urlparse(a.add_blog).netloc],
             'url': a.add_blog, 'auto': {'topics': T.tag_topics(a.title, ''), 'unitree': []}, 'added': today}
        log('加入博客 %s：%s' % (bid, a.title))
        if not a.dry_run:
            T.save_papers(papers + [p])
        return

    if a.add:
        ids = []
        for raw_id in a.add:
            m = T.ARXIV_ID.search(raw_id)
            if not m:
                log('不是 arXiv 编号，跳过：' + raw_id)
            elif m.group(1) in {p['id'] for p in papers}:
                log('库里已经有了：' + m.group(1))
            else:
                ids.append(m.group(1))
        meta = arxiv_by_id(ids)
        new = [meta[i] for i in ids if i in meta]
        for i in ids:
            if i not in meta:
                log('arXiv 上没查到：' + i)
    else:
        new = []
        if not a.no_search:
            log('检索新论文')
            new = search_new(src, known, today)

    for r in new:
        p = make_paper(r, lib_titles, refs, today)
        papers.append(p)
        added.append(p)
        known.add(p['id'])
        lib_titles[p['id']] = T.norm(p['title'])
        log('  + %s  %s  %s' % (p['id'], p['date'], p['title'][:70]))

    if not a.add and not a.no_search:
        log('回溯引用')
        for r in backtrack(src, refs, known):
            p = make_paper(r, lib_titles, refs, today)
            papers.append(p)
            added.append(p)
            known.add(p['id'])
            lib_titles[p['id']] = T.norm(p['title'])

    changed = bool(added)
    if not a.add and not a.no_signals and not a.dry_run:
        log('刷新发表去向')
        changed = bool(refresh_venues(papers, today)) or changed
    if a.dry_run:
        log('（--dry-run：不刷新被引数和 stars）')
    elif not a.no_signals:
        log('刷新被引数和 stars')
        only = {p['id'] for p in added} if a.add else None
        changed = refresh_signals(papers, sig, refs, today, only) or changed

    log('\n新增 %d 篇，库里现有 %d 条。' % (len(added), len(papers)))
    if a.dry_run:
        log('（--dry-run：没有写文件）')
        return
    if changed:
        sig['updated'] = today
    T.save_papers(papers)
    T.save_signals(sig)
    T.save_refs(refs)


if __name__ == '__main__':
    main()
