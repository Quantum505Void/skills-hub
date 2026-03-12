#!/usr/bin/env python3
"""
Build script: pre-fetch all data and inject into index.html as static JSON.
Run by GitHub Actions on every push to main.
"""
import json, time, urllib.request, urllib.error, os, re, sys

PROXY = 'https://xiaoxin-clawhub-mirror.moke521-wang.workers.dev'
GH_TOKEN = os.environ.get('GH_TOKEN', '')

def fetch(url, retries=3):
    headers = {'User-Agent': 'skills-hub-builder/1.0'}
    if GH_TOKEN and 'api.github.com' in url:
        headers['Authorization'] = f'token {GH_TOKEN}'
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except Exception as e:
            print(f'  [warn] fetch {url}: {e}', file=sys.stderr)
            if i < retries - 1:
                time.sleep(2)
    return None

def fetch_clawhub():
    items = []
    cursor = None
    page = 0
    while page < 10:  # max 10 pages = 480 skills
        url = f'{PROXY}/api/v1/skills?limit=48&orderBy=updatedAt'
        if cursor:
            url += f'&cursor={urllib.parse.quote(cursor)}'
        data = fetch(url)
        if not data:
            break
        batch = data.get('items', [])
        for s in batch:
            items.append({
                'id': s['slug'],
                'name': s.get('displayName') or s['slug'],
                'slug': s['slug'],
                'desc': s.get('summary') or '',
                'stars': s.get('stats', {}).get('stars', 0),
                'downloads': s.get('stats', {}).get('downloads', 0),
                'version': (s.get('latestVersion') or {}).get('version', ''),
                'source': 'clawhub',
                'install': f'CLAWHUB_REGISTRY={PROXY} clawhub install {s["slug"]}',
                'installOfficial': f'clawhub install {s["slug"]}',
                'url': f'https://clawhub.ai/skills/{s["slug"]}',
            })
        cursor = data.get('nextCursor')
        if not cursor:
            break
        page += 1
        time.sleep(0.3)
    print(f'  clawhub: {len(items)} skills')
    return items

def fetch_github_repo(repo):
    import urllib.parse
    data = fetch(f'https://api.github.com/repos/{repo}')
    if not data or 'full_name' not in data:
        return None
    return data

FEATURED_REPOS = [
    ('anthropics/skills',                    'Public repository for Agent Skills — official Anthropic skills catalog.'),
    ('vercel-labs/agent-skills',             "Vercel's official collection of agent skills for Next.js, v0, and more."),
    ('openai/skills',                        'Skills Catalog for Codex — official OpenAI agent skills.'),
    ('vercel-labs/skills',                   'The open agent skills tool - npx skills.'),
    ('github/awesome-copilot',               'Community-contributed instructions, agents, skills, and configurations for GitHub Copilot.'),
    ('googleworkspace/cli',                  'Google Workspace CLI — one command-line tool for Drive, Gmail, Docs, Sheets, and more.'),
    ('VoltAgent/awesome-openclaw-skills',    'The awesome collection of OpenClaw skills. 5,400+ skills filtered and curated.'),
    ('ComposioHQ/awesome-claude-skills',     'A curated list of awesome Claude Skills, resources, and tools for customizing AI agent behavior.'),
    ('hesreallyhim/awesome-claude-code',     'Curated list of awesome skills, hooks, slash-commands, agent orchestration, and more.'),
    ('sickn33/antigravity-awesome-skills',   'The Ultimate Collection of 1000+ Agentic Skills for Claude Code/Antigravity/OpenClaw.'),
    ('VoltAgent/awesome-agent-skills',       'Claude Code Skills and 500+ agent skills from official dev teams and the community.'),
    ('travisvn/awesome-claude-skills',       'A curated list of awesome Claude Skills, resources, and tools for customizing AI.'),
    ('BehiSecc/awesome-claude-skills',       'A curated list of Claude Skills covering common workflows and integrations.'),
    ('heilcheng/awesome-agent-skills',       'Curated list of skills, tools, tutorials, and capabilities for AI coding agents.'),
    ('code-yeongyu/oh-my-openagent',         'oh-my-openagent (omo) — the best agent harness with skill management.'),
    ('thedotmack/claude-mem',                'A Claude Code plugin that automatically captures everything and builds persistent memory.'),
    ('agentskills/agentskills',              'Specification and documentation for the Agent Skills open standard (SKILL.md).'),
    ('yusufkaraaslan/Skill_Seekers',         'Convert documentation websites, GitHub repos, and PDFs into reusable agent skills.'),
    ('JimLiu/baoyu-skills',                  '包括小红书、微信公众号、漫画生成等中文内容创作 agent skills.'),
    ('Jeffallan/claude-skills',              '66 Specialized Skills for Full-Stack Developers — transforms Claude into a senior engineer.'),
    ('Orchestra-Research/AI-Research-SKILLs','Comprehensive open-source library of AI research and engineering agent skills.'),
    ('refly-ai/refly',                       'The first open-source agent skills builder. Define skills by recording your workflows.'),
    ('phuryn/pm-skills',                     'PM Skills Marketplace: 100+ agentic skills, commands, and plugins for product managers.'),
    ('OthmanAdi/planning-with-files',        'Claude Code skill implementing Manus-style persistent markdown planning.'),
    ('K-Dense-AI/claude-scientific-skills',  'Ready-to-use agent skills for research, science, engineering, and analysis.'),
    ('trailofbits/skills',                   'Trail of Bits skills for security research and vulnerability detection.'),
    ('arpitg1304/robotics-agent-skills',     'Agent skills that make AI coding assistants write production-ready robotics code.'),
    ('FrancyJGLisboa/agent-skill-creator',   'Turn any workflow into reusable AI agent skills that install via skills.sh.'),
    ('kepano/obsidian-skills',               'Agent skills for Obsidian. Teach your agent to use Markdown, Bases, JSON Canvas, and more.'),
    ('alirezarezvani/claude-skills',         '+180 production-ready skills & plugins for Claude Code, OpenAI Codex, and OpenClaw.'),
    ('davepoon/buildwithclaude',             'A single hub to find Claude Skills, Agents, Commands, Hooks, Plugins, and Marketplace resources.'),
    ('NevaMind-AI/memU',                     'Memory for 24/7 proactive agents like OpenClaw (moltbot, claudia).'),
    ('wshobson/agents',                      'Production-ready agent skills for Claude Code, OpenClaw, and compatible AI frameworks.'),
    ('remotion-dev/skills',                  'Agent Skills for Remotion — create and edit videos with AI agents.'),
    ('doanbactam/agent-skills-directory',    'Browse SKILL.md files for Claude, Cursor, Windsurf and other AI coding assistants.'),
]

def fetch_all_repos():
    import urllib.parse
    items = []
    for repo, fallback_desc in FEATURED_REPOS:
        print(f'  fetching {repo}...', file=sys.stderr)
        info = fetch_github_repo(repo)
        if not info:
            # use fallback
            items.append({
                'id': repo,
                'name': repo,
                'slug': repo,
                'desc': fallback_desc,
                'stars': 0,
                'downloads': 0,
                'version': '',
                'source': 'github',
                'install': f'git clone https://github.com/{repo}',
                'installOfficial': f'git clone https://github.com/{repo}',
                'url': f'https://github.com/{repo}',
            })
            continue
        items.append({
            'id': repo,
            'name': info.get('full_name', repo),
            'slug': repo,
            'desc': info.get('description') or fallback_desc,
            'stars': info.get('stargazers_count', 0),
            'downloads': 0,
            'version': '',
            'source': 'github',
            'install': f'git clone https://github.com/{repo}',
            'installOfficial': f'git clone https://github.com/{repo}',
            'url': info.get('html_url', f'https://github.com/{repo}'),
        })
        time.sleep(0.2)
    items.sort(key=lambda x: x['stars'], reverse=True)
    print(f'  github repos: {len(items)} items')
    return items

def fetch_skillssh():
    import urllib.parse
    url = 'https://api.github.com/search/repositories?q=skills.sh+agent+skills&sort=stars&per_page=30'
    data = fetch(url)
    if not data:
        return []
    items = []
    for r in (data.get('items') or []):
        items.append({
            'id': 'gh:' + r['full_name'],
            'name': r['full_name'],
            'slug': r['full_name'],
            'desc': r.get('description') or '',
            'stars': r.get('stargazers_count', 0),
            'downloads': 0,
            'version': '',
            'source': 'skillssh',
            'install': f"npx skills add {r['full_name'].split('/')[0]}/{r['name']}@latest --yes",
            'installOfficial': f"npx skills add {r['full_name'].split('/')[0]}/{r['name']}@latest --yes",
            'url': r.get('html_url', ''),
        })
    print(f'  skillssh: {len(items)} items')
    return items

import urllib.parse

print('Fetching ClawHub...', file=sys.stderr)
clawhub_data = fetch_clawhub()

print('Fetching GitHub repos...', file=sys.stderr)
github_data = fetch_all_repos()

# awesome = github data filtered to awesome/official repos (already in github_data)
awesome_data = [x for x in github_data]  # same set, sorted by stars

print('Fetching skills.sh repos...', file=sys.stderr)
skillssh_data = fetch_skillssh()

payload = {
    'clawhub': clawhub_data,
    'github': github_data,
    'awesome': awesome_data,
    'skillssh': skillssh_data,
    'builtAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
}

# Read index.html and inject
with open('index.html', 'r') as f:
    html = f.read()

json_str = json.dumps(payload, ensure_ascii=False)

# Replace or inject the STATIC_DATA block
marker_start = '/* STATIC_DATA_START */'
marker_end = '/* STATIC_DATA_END */'
new_block = f'{marker_start}\nconst STATIC_DATA = {json_str};\n{marker_end}'

if marker_start in html:
    html = re.sub(
        re.escape(marker_start) + r'.*?' + re.escape(marker_end),
        new_block, html, flags=re.DOTALL
    )
else:
    html = html.replace('<script>', '<script>\n' + new_block + '\n', 1)

with open('index.html', 'w') as f:
    f.write(html)

print(f'Done. clawhub={len(clawhub_data)}, github={len(github_data)}, skillssh={len(skillssh_data)}')
