# -*- coding: utf-8 -*-
"""共享代码：读写数据文件、解析批注、关键词标注、合成页面数据。只依赖标准库。"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
NOTES = os.path.join(ROOT, 'notes')
DOCS = os.path.join(ROOT, 'docs')
STATUS = ['unread', 'queue', 'read']  # 页面上显示为 未读 / 待读 / 已读
ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$')

# ---------------------------------------------------------------- 标注规则
# 这些规则只看关键词，会有错。某一篇标错了，在它的批注文件里写 topics: [...] 覆盖。

# 方向：匹配标题 + 摘要（小写）。'基准与评测' 另有规则，见 tag_topics。
TOPICS = [
    ('Harness 与接口', r'harness|robot-use interface|(action|control|visual) interface'),
    ('代码即策略', r'code[- ]as[- ]polic|coding agents?|program synthesis|polic(y|ies) code'
                   r'|writes? (executable )?(code|programs)|\bcap-'),
    ('自演化', r'self-evolv|self-improv|recursive|\brsi\b|skill librar|skills? discovery|evolv|lifelong|continual'),
    ('后训练', r'post-train|distill|grpo|open-weight|supervised fine-tuning|\bsft\b|agentic (reinforcement|rl)'),
    ('基准与评测', None),
    ('安全', r'safety|\bunsafe|\brisks?\b|attack|injection|refus|jailbreak|emergency stop|hazard'),
    ('人形与腿足', r'humanoid|whole-body|loco-manip|legged|quadruped|unitree|biped'),
    ('涉及 VLA', r'\bvlas?\b|vision-language-action'),
    ('导航', r'navigation|\bvln\b'),
    ('记忆与上下文', r'\bmemory\b|in-context'),
    ('综述与观点', r'\bsurvey|\breview of|roadmap|position paper|perspective|taxonomy|primer'),
]
# 以下三组匹配正文（去掉参考文献之后）。
UNITREE = [
    ('G1', r'Unitree\W{0,3}G1(?![- ]?D\b)'),
    ('H1-2', r'\bH1[-_]2\b'),
    ('H1', r'Unitree\W{0,3}H1\b(?![-_]2)'),
    ('R1', r'Unitree\W{0,3}R1\b(?![- ]?D\b)'),
    ('H2', r'Unitree\W{0,3}H2\b(?![- ]?(?:D\b|Plus))'),
    ('H2 Plus', r'H2[- ]Plus'),
    ('G1-D', r'\bG1[- ]D\b'),
    ('R1-D', r'Unitree\W{0,3}R1[- ]?D\b'),
    ('H2-D', r'\bH2[- ]D\b'),
]
BENCHMARKS = [  # 出现两次以上才算
    ('LIBERO-PRO', r'LIBERO[- ]P(RO|ro)'),
    ('LIBERO', r'LIBERO(?![- ]?(PRO|Pro|Plus|plus|Agent|RECOVER))'),
    ('RoboDojo', r'RoboDojo'), ('RoboCasa', r'RoboCasa'), ('RoboTwin', r'RoboTwin'),
    ('CaP-Bench', r'CaP-(Bench|Gym)'), ('ManiSkill', r'ManiSkill'), ('SimplerEnv', r'SimplerEnv'),
    ('BEHAVIOR', r'BEHAVIOR(-1K)?\b'), ('CALVIN', r'CALVIN'), ('Meta-World', r'Meta-?World'),
    ('RLBench', r'RLBench'), ('R2R', r'\bR2R\b'), ('VLABench', r'VLABench'),
]
MODELS = [  # 出现两次以上才算
    ('GPT-6', r'GPT-6'), ('GPT-5', r'GPT-5'), ('Claude', r'Claude'), ('Gemini', r'Gemini'),
    ('Qwen', r'Qwen'), ('DeepSeek', r'DeepSeek'), ('Codex', r'\bCodex\b'), ('Claude Code', r'Claude Code'),
]


def tag_topics(title, abstract):
    txt = (title + ' ' + abstract).lower()
    out = [name for name, pat in TOPICS if pat and re.search(pat, txt)]
    if (re.search(r'bench|evaluat|\bstudy\b|audit|\bexam\b|profiling', title.lower())
            or re.search(r'(introduce|present|propose|release|develop|build)[^.]{0,90}benchmark', txt)):
        out.append('基准与评测')
    order = [name for name, _ in TOPICS]
    return sorted(set(out), key=order.index)


def tag_fulltext(body):
    return {
        'unitree': [n for n, p in UNITREE if re.search(p, body)],
        'benchmarks': [n for n, p in BENCHMARKS if len(re.findall(p, body)) >= 2],
        'models': [n for n, p in MODELS if len(re.findall(p, body)) >= 2],
    }


# ---------------------------------------------------------------- 文本处理
def strip_tags(s, keep_math=False):
    s = re.sub(r'(?is)<(script|style)\b.*?</\1>' if keep_math else r'(?is)<(script|style|math)\b.*?</\1>', ' ', s)
    return ' '.join(html.unescape(re.sub(r'(?s)<[^>]+>', ' ', s)).split())


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


def clean_title(t):
    """把 $π_{0.5}$ 这类 TeX 片段化成普通文字。"""
    def tex(m):
        return re.sub(r'[{}_^\s]', '', re.sub(r'\\[a-zA-Z]+', '', m.group(1)))
    return ' '.join(re.sub(r'\$([^$]*)\$', tex, t).split())


def excerpt(abstract, limit=380):
    out = ''
    for s in re.split(r'(?<=[.!?])\s+', abstract or ''):
        if out and len(out) + len(s) > limit:
            break
        out += (' ' if out else '') + s
    return out


def split_fulltext(raw):
    """arXiv HTML -> 正文文字、参考文献条目、正文里的 GitHub 链接。"""
    k = raw.find('ltx_bibliography')
    body_html, bib_html = (raw[:k], raw[k:]) if k >= 0 else (raw, '')
    # 参考文献里保留公式的文字：标题带符号的论文（比如 π0）要靠它按标题匹配
    entries = [strip_tags(x.split('</li>')[0], keep_math=True)
               for x in re.split(r'<li[^>]*class="[^"]*ltx_bibitem[^"]*"[^>]*>', bib_html)[1:]]
    links = []
    for g in re.findall(r'github\.com/[\w.-]+/[\w.-]+', body_html):
        g = g.rstrip('.')
        if g not in links and 'latexml' not in g.lower() and not g.endswith('/arXiv'):
            links.append(g)
    return strip_tags(body_html), entries, links


ARXIV_ID = re.compile(r'(?<![\d.])(\d{4}\.\d{4,5})(?:v\d+)?(?!\d)')


def refs_of(entries, lib_titles):
    """一篇论文的参考文献 -> 它引用的 arXiv 编号。
    有编号的直接取；没编号的条目按标题匹配库内论文（标题规范化后不少于 28 个字符才匹配）。"""
    out = set()
    for e in entries:
        out.update(ARXIV_ID.findall(e))
        en = norm(e)
        for pid, tn in lib_titles.items():
            if len(tn) >= 28 and tn in en:
                out.add(pid)
    return out


# ---------------------------------------------------------------- 数据文件
def _read_json(name, default):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def load_papers():
    out = []
    p = os.path.join(DATA, 'papers.jsonl')
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    out.append(json.loads(line))
    return out


def save_papers(papers):
    with open(os.path.join(DATA, 'papers.jsonl'), 'w', encoding='utf-8') as f:
        for p in papers:
            f.write(json.dumps(p, ensure_ascii=False) + '\n')


def load_signals():
    return _read_json('signals.json', {'updated': '', 'papers': {}})


def load_refs():
    return _read_json('refs.json', {'refs': {}, 'skipped': []})


def load_sources():
    return _read_json('sources.json', {})


def _dump_map(d):
    """一个键一行，方便看 git diff。"""
    rows = ['  %s: %s' % (json.dumps(k), json.dumps(d[k], ensure_ascii=False, separators=(',', ':')))
            for k in sorted(d)]
    return '{\n' + ',\n'.join(rows) + '\n }'


def save_signals(sig):
    with open(os.path.join(DATA, 'signals.json'), 'w', encoding='utf-8') as f:
        f.write('{\n "updated": %s,\n "papers": %s\n}\n' % (json.dumps(sig.get('updated', '')), _dump_map(sig['papers'])))


def save_refs(refs):
    refs = {'refs': {k: sorted(v) for k, v in refs['refs'].items()}, 'skipped': sorted(set(refs.get('skipped', [])))}
    with open(os.path.join(DATA, 'refs.json'), 'w', encoding='utf-8') as f:
        f.write('{\n "refs": %s,\n "skipped": %s\n}\n' % (_dump_map(refs['refs']), json.dumps(refs['skipped'])))


def load_ignore():
    p = os.path.join(DATA, 'ignore.txt')
    out = set()
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            for line in f:
                line = line.split('#')[0].strip()
                if line:
                    out.add(line.split()[0])
    return out


# ---------------------------------------------------------------- 批注
def read_note(pid):
    """notes/<id>.md -> {'status', 'reads', 'batch', 'topics', 'body', 'extra'}；没有文件返回 None。
    reads 是读过几遍；状态是已读而没写遍数的，算 1 遍。"""
    p = os.path.join(NOTES, pid + '.md')
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        txt = f.read().replace('\r\n', '\n')
    note = {'status': 'unread', 'reads': 0, 'batch': '', 'topics': [], 'body': '', 'extra': []}
    body = txt
    if txt.startswith('---\n'):
        end = txt.find('\n---', 3)
        if end > 0:
            for line in txt[4:end].split('\n'):
                if ':' not in line:
                    continue
                k, v = line.split(':', 1)
                k, v = k.strip(), v.strip()
                if k == 'status':
                    note['status'] = v if v in STATUS else 'unread'
                elif k == 'reads':
                    note['reads'] = int(v) if v.isdigit() else 0
                elif k == 'batch':
                    note['batch'] = v
                elif k == 'topics':
                    note['topics'] = [x.strip().strip('"\'') for x in v.strip('[]').split(',') if x.strip()]
                else:
                    note['extra'].append((k, v))
            body = txt[end + 4:]
    note['body'] = body.strip('\n')
    note['reads'] = max(1, note['reads']) if note['status'] == 'read' else 0
    return note


def write_note(pid, status=None, body=None, reads=None):
    """写状态、遍数和正文，保留文件里已有的 batch、topics 和其他字段。没有内容可写时删掉文件。
    遍数大于 0 时状态一定是已读；状态不是已读时遍数归零。"""
    if not ID_RE.match(pid):
        raise ValueError('不合法的编号：%r' % pid)
    note = read_note(pid) or {'status': 'unread', 'reads': 0, 'batch': '', 'topics': [], 'body': '', 'extra': []}
    if status is not None:
        if status not in STATUS:
            raise ValueError('status 只能是 %s' % ' / '.join(STATUS))
        note['status'] = status
    if reads is not None:
        if isinstance(reads, bool) or not isinstance(reads, int) or not 0 <= reads <= 99:
            raise ValueError('reads 要是 0 到 99 的整数')
        note['reads'] = reads
        if reads > 0:
            note['status'] = 'read'
        elif note['status'] == 'read':
            note['status'] = 'unread'
    note['reads'] = max(1, note['reads']) if note['status'] == 'read' else 0
    if body is not None:
        note['body'] = body.replace('\r\n', '\n').strip('\n')
    p = os.path.join(NOTES, pid + '.md')
    if note['status'] == 'unread' and not (note['body'] or note['batch'] or note['topics'] or note['extra']):
        if os.path.exists(p):
            os.remove(p)
        return
    head = ['status: ' + note['status']]
    if note['reads'] > 1:   # 读过一遍不用写，status: read 就表示一遍
        head.append('reads: %d' % note['reads'])
    if note['batch']:
        head.append('batch: ' + note['batch'])
    if note['topics']:
        head.append('topics: [%s]' % ', '.join(note['topics']))
    head += ['%s: %s' % kv for kv in note['extra']]
    os.makedirs(NOTES, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write('---\n' + '\n'.join(head) + '\n---\n' + (note['body'] + '\n' if note['body'] else ''))


# ---------------------------------------------------------------- 合成页面数据
def build_data():
    site = load_sources().get('site', {})
    sig = load_signals()
    ignore = load_ignore()
    tags = [name for name, _ in TOPICS]
    items = []
    asof = sig.get('updated', '')
    for p in load_papers():
        if p['id'] in ignore:
            continue
        note = read_note(p['id'])
        n = note or {}
        s = sig['papers'].get(p['id'], {})
        auto = p.get('auto', {})
        g = []
        for t in (n.get('topics') or auto.get('topics', [])):
            if t not in tags:
                tags.append(t)
            g.append(tags.index(t))
        authors = p.get('authors') or ['?']
        it = {
            'i': p['id'], 'k': 'b' if p.get('type') == 'blog' else 'p',
            't': clean_title(p['title']), 'd': p['date'], 'a': authors[0], 'n': len(authors),
            'x': excerpt(p.get('abstract', '')), 'g': sorted(set(g)),
            'u': auto.get('unitree', []), 'b': auto.get('benchmarks', []), 'm': auto.get('models', []),
            'c': s.get('cited_in_library'), 's': s.get('s2'), 'r': s.get('stars'),
            'p': p.get('repo', ''), 'v': p.get('venue', ''),
            'st': STATUS.index(n.get('status', 'unread')), 'rc': n.get('reads', 0),
            'nt': n.get('body', ''), 'bt': n.get('batch', ''),
            'ft': bool(p.get('fulltext')),
        }
        if p.get('url'):
            it['l'] = p['url']
        items.append(it)
        asof = max(asof, p.get('added', ''))
    items.sort(key=lambda x: x['d'], reverse=True)
    # 精读清单的批次：sources.json 里排好的在前，批注文件里新写的批次名排在后面
    seen = {x['bt'] for x in items if x['bt']}
    order = site.get('batches', [])
    batches = [b for b in order if b in seen] + sorted(seen - set(order))
    return {
        'asof': asof, 'repo': site.get('repo', ''), 'branch': site.get('branch', 'main'),
        'bat': batches, 'tags': tags, 'uni': [n for n, _ in UNITREE],
        'ben': [n for n, _ in BENCHMARKS], 'mod': [n for n, _ in MODELS], 'items': items,
    }


def build_js():
    js = json.dumps(build_data(), ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return 'window.TRACKER_DATA=' + js + ';\n'


def build():
    os.makedirs(DOCS, exist_ok=True)
    js = build_js()
    with open(os.path.join(DOCS, 'data.js'), 'w', encoding='utf-8') as f:
        f.write(js)
    return len(js)
