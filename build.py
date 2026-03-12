#!/usr/bin/env python3
"""
Build script: pre-fetch all data and inject into index.html as static JSON.
Run by GitHub Actions on every push to main.
"""
import json, time, urllib.request, urllib.error, urllib.parse, os, re, sys

PROXY = 'https://xiaoxin-clawhub-mirror.moke521-wang.workers.dev'
GH_TOKEN = os.environ.get('GH_TOKEN', '')

# Category keyword rules
CATEGORY_RULES = [
    ('🤖 AI/ML',        ['llm', 'rag', 'embedding', 'vector', 'openai', 'claude', 'gemini', 'gpt',
                         'diffusion', 'machine-learning', 'neural', 'inference', 'ai-', 'ai_',
                         'agent-browser', 'agent-tools', 'ai-automation', 'ai-image', 'ai-music',
                         'ai-podcast', 'ai-avatar', 'ai-content', 'ai-marketing', 'ai-product',
                         'ai-rag', 'academic-deep-research', 'agent-md', 'agentic', 'perplexity',
                         'deep-research', 'paper-recommendation', 'prompt-lookup', 'image-generation',
                         'background-remove', 'icon-generation', 'product-photography', 'canvas-design',
                         'algorithmic-art', 'visual-design-foundations']),
    ('🧩 Agent模式',    ['debug-council', 'parallel-builder', 'dispatching-parallel-agents',
                         'subagent-driven', 'multi-reviewer', 'parallel-feature', 'executing-plans',
                         'planning-with-files', 'session-handoff', 'finishing-a-development',
                         'requesting-code-review', 'verification-before-completion',
                         'requirements-clarity', 'ask-questions-if-underspecified',
                         'reducing-entropy', 'using-superpowers', 'track-management',
                         'code-review-excellence', 'systematic-debugging', 'error-handling-patterns',
                         'naming-analyzer', 'feedback-mastery', 'on-call-handoff',
                         'incident-runbook', 'auto-monitor']),
    ('💻 编程语言/框架', ['rust', 'golang', 'go-concurrency', 'typescript-advanced', 'godot',
                         'gdscript', 'expo', 'use-dom', 'upgrading-expo', 'expo-api',
                         'shopify', 'stripe', 'mui', 'marp', 'mermaid', 'regex-patterns',
                         'dependency-updater', 'dependency-upgrade', 'monorepo', 'nx',
                         'data-visualization', 'backtesting', 'event-store', 'cost-optimization',
                         'linux', 'network-scanner']),
    ('⛓ 区块链/Web3',   ['blockchain', 'defi', 'web3', 'smart-contract', 'solidity', 'nft',
                         'token', 'staking', 'amm', 'hardhat', 'foundry', 'semgrep']),
    ('📊 产品/商业',     ['pitch-deck', 'market-researcher', 'market-sizing', 'competitive-intel',
                         'competitive-landscape', 'competitor-teardown', 'product-hunt',
                         'product-engineer', 'product-changelog', 'review-analyst',
                         'startup-financial', 'finance-accounting', 'real-estate',
                         'team-composition', 'employment-contract', 'patent-lawyer',
                         'travel-manager', 'language-learning']),
    ('📚 知识/学科',     ['astronomy', 'biology', 'chemistry', 'economics', 'geography', 'history',
                         'law', 'literature', 'math', 'philosophy', 'sociology', 'academic']),
    ('🌿 生活方式',      ['fitness', 'nutrition', 'sleep', 'cooking', 'parenting', 'mindfulness',
                         'meditation', 'health', 'wellness']),
    ('🎨 前端',         ['vue', 'react', 'next', 'tailwind', 'css', 'electron', 'shadcn',
                         'accessibility', 'svelte', 'angular', 'nuxt', 'vite', 'webpack',
                         'html', 'ui-component', 'frontend', 'animation', 'motion']),
    ('🐍 Python',       ['python', 'fastapi', 'django', 'flask', 'pandas', 'pytest', 'uv-python',
                         'pip', 'pydantic', 'sqlalchemy']),
    ('⚙️ 后端/数据库',  ['node', 'rest', 'graphql', 'redis', 'postgres', 'mongodb', 'backend',
                         'express', 'nestjs', 'prisma', 'drizzle', 'supabase', 'firebase',
                         'mysql', 'sqlite', 'orm', 'database', 'sql-']),
    ('🚀 DevOps',       ['docker', 'k8s', 'kubernetes', 'terraform', 'github-action', 'ci-',
                         'deploy', 'monitoring', 'prometheus', 'grafana', 'ansible', 'helm',
                         'devops', 'pipeline', 'gitops', 'slo', 'sre']),
    ('🔒 安全',         ['security', 'auth', 'jwt', 'pentest', 'audit', 'reverse', 'oauth',
                         'ssl', 'tls', 'vulnerability', 'exploit', 'penetration', 'gdpr', 'pci', 'compliance']),
    ('📝 内容创作',      ['blog', 'seo', 'writing', 'content', 'social', 'marketing', 'copywriting',
                         'newsletter', 'podcast', 'video', 'youtube', 'twitter', 'instagram',
                         'tiktok', 'xiaohongshu', 'baoyu', 'academic-citation', 'academic-writing']),
    ('🛠 工具',         ['git', 'shell', 'tmux', 'vim', 'productivity', 'cli', 'terminal', 'bash',
                         'zsh', 'obsidian', 'notion', 'jira', 'github', 'workflow', 'automation',
                         '1password', 'spotify', 'slack', 'feishu', 'discord']),
    ('📱 移动端',        ['ios', 'android', 'react-native', 'flutter', 'swift', 'kotlin', 'mobile']),
    ('🏗 架构',          ['microservice', 'cqrs', 'event-sourcing', 'adr', 'api-design', 'architecture',
                         'ddd', 'clean-arch', 'hexagonal']),
    ('🐾 OpenClaw',     ['openclaw', 'mcp', 'sag', 'whisper', 'gog', 'acp-router', 'skill-creator',
                         'clawhub', 'oracle', 'healthcheck', 'session-logs']),
]

def categorize(name, desc):
    text = (name + ' ' + desc).lower()
    for cat, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw in text:
                return cat
    return '📦 其他'


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
    while page < 10:
        url = f'{PROXY}/api/v1/skills?limit=48&orderBy=updatedAt'
        if cursor:
            url += f'&cursor={urllib.parse.quote(cursor)}'
        data = fetch(url)
        if not data:
            break
        batch = data.get('items', [])
        for s in batch:
            name = s.get('displayName') or s['slug']
            desc = s.get('summary') or ''
            items.append({
                'id': s['slug'],
                'name': name,
                'slug': s['slug'],
                'desc': desc,
                'stars': s.get('stats', {}).get('stars', 0),
                'downloads': s.get('stats', {}).get('downloads', 0),
                'version': (s.get('latestVersion') or {}).get('version', ''),
                'source': 'clawhub',
                'install': f'CLAWHUB_REGISTRY={PROXY} clawhub install {s["slug"]}',
                'installOfficial': f'clawhub install {s["slug"]}',
                'url': f'https://clawhub.ai/skills/{s["slug"]}',
                'category': categorize(s['slug'], desc),
            })
        cursor = data.get('nextCursor')
        if not cursor:
            break
        page += 1
        time.sleep(0.3)
    print(f'  clawhub: {len(items)} skills')
    return items

def fetch_github_repo(repo):
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
    items = []
    for repo, fallback_desc in FEATURED_REPOS:
        print(f'  fetching {repo}...', file=sys.stderr)
        info = fetch_github_repo(repo)
        desc = (info.get('description') if info else None) or fallback_desc
        name = (info.get('full_name') if info else None) or repo
        stars = (info.get('stargazers_count', 0) if info else 0)
        url = (info.get('html_url') if info else None) or f'https://github.com/{repo}'
        items.append({
            'id': repo,
            'name': name,
            'slug': repo,
            'desc': desc,
            'stars': stars,
            'downloads': 0,
            'version': '',
            'source': 'github',
            'install': f'git clone https://github.com/{repo}',
            'installOfficial': f'git clone https://github.com/{repo}',
            'url': url,
            'category': categorize(repo, desc),
        })
        time.sleep(0.2)
    items.sort(key=lambda x: x['stars'], reverse=True)
    print(f'  github repos: {len(items)} items')
    return items

def fetch_skillssh():
    url = 'https://api.github.com/search/repositories?q=skills.sh+agent+skills&sort=stars&per_page=30'
    data = fetch(url)
    if not data:
        return []
    items = []
    for r in (data.get('items') or []):
        name = r['full_name']
        desc = r.get('description') or ''
        items.append({
            'id': 'gh:' + name,
            'name': name,
            'slug': name,
            'desc': desc,
            'stars': r.get('stargazers_count', 0),
            'downloads': 0,
            'version': '',
            'source': 'skillssh',
            'install': f"npx skills add {r['full_name'].split('/')[0]}/{r['name']}@latest --yes",
            'installOfficial': f"npx skills add {r['full_name'].split('/')[0]}/{r['name']}@latest --yes",
            'url': r.get('html_url', ''),
            'category': categorize(name, desc),
        })
    print(f'  skillssh: {len(items)} items')
    return items

def fetch_local_skills():
    """Parse skills-catalog.md and return list of locally installed skills."""
    catalog_path = '/home/void/.openclaw/workspace/memory/skills-catalog.md'
    items = []
    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f'  [warn] cannot read skills-catalog.md: {e}', file=sys.stderr)
        return []

    # Split by skill entries
    # Format: ## skill: <name>\n<description>
    pattern = re.compile(r'^## skill:\s*(.+?)$', re.MULTILINE)
    matches = list(pattern.finditer(content))

    for i, m in enumerate(matches):
        skill_name = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        desc_block = content[start:end].strip()
        # Clean up desc: take first non-empty paragraph, limit length
        desc = desc_block.split('\n\n')[0].replace('\n', ' ').strip()
        if len(desc) > 300:
            desc = desc[:297] + '...'

        items.append({
            'id': 'local:' + skill_name,
            'name': skill_name,
            'slug': skill_name,
            'desc': desc,
            'stars': 0,
            'downloads': 0,
            'version': '',
            'source': 'local',
            'install': f'# Already installed at workspace/skills/{skill_name}',
            'installOfficial': f'clawhub install {skill_name}',
            'url': f'https://clawhub.ai/skills/{skill_name}',
            'category': categorize(skill_name, desc),
        })

    items.sort(key=lambda x: x['name'])
    print(f'  local skills: {len(items)} items')
    return items


print('Fetching ClawHub...', file=sys.stderr)
clawhub_data = fetch_clawhub()

print('Fetching GitHub repos...', file=sys.stderr)
github_data = fetch_all_repos()

awesome_data = list(github_data)

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

# Use application/json tag to avoid any JS syntax issues with embedded data
# json.dumps handles all control chars (\n, \r, \t etc), and </script> inside
# a type="application/json" block is safe (browser won't execute it).
json_str = json.dumps(payload, ensure_ascii=True)

sd_start = '<!-- STATIC_DATA_START -->'
sd_end = '<!-- STATIC_DATA_END -->'
new_block = f'{sd_start}\n<script type="application/json" id="sd">{json_str}</script>\n{sd_end}'

if sd_start in html:
    html = re.sub(
        re.escape(sd_start) + r'.*?' + re.escape(sd_end),
        lambda m: new_block, html, flags=re.DOTALL
    )
else:
    # fallback: replace old marker style
    marker_start = '/* STATIC_DATA_START */'
    marker_end = '/* STATIC_DATA_END */'
    old_script_block = re.search(
        r'<script>\s*' + re.escape(marker_start) + r'.*?' + re.escape(marker_end) + r'\s*',
        html, flags=re.DOTALL
    )
    if old_script_block:
        html = html[:old_script_block.start()] + new_block + '\n' + html[old_script_block.end():]
    else:
        html = html.replace('</head>', new_block + '\n</head>', 1)

with open('index.html', 'w') as f:
    f.write(html)

print(f'Done. clawhub={len(clawhub_data)}, github={len(github_data)}, skillssh={len(skillssh_data)}')
