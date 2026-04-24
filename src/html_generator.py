import re
from html import escape
from pathlib import Path
from typing import Dict, List, Any

def parse_unified_diff(diff_text: str) -> Dict[str, List[Dict[str, Any]]]:
    files_diffs = {}
    current_file = None
    old_ln = 0
    new_ln = 0
    
    lines = diff_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('diff --git'):
            match = re.search(r' b/(.*)$', line)
            if match:
                current_file = match.group(1)
                files_diffs[current_file] = []
            i += 1
        elif current_file:
            if line.startswith('---') or line.startswith('+++'):
                i += 1
                continue
            if line.startswith('@@'):
                m = re.search(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
                if m:
                    old_ln = int(m.group(1))
                    new_ln = int(m.group(2))
                files_diffs[current_file].append({'type': 'header', 'text': line})
                i += 1
            elif line.startswith(' '):
                files_diffs[current_file].append({
                    'type': 'ctx',
                    'old_ln': old_ln,
                    'new_ln': new_ln,
                    'old_text': line[1:],
                    'new_text': line[1:]
                })
                old_ln += 1
                new_ln += 1
                i += 1
            elif line.startswith('+') or line.startswith('-'):
                dels = []
                adds = []
                while i < len(lines) and (lines[i].startswith('+') or lines[i].startswith('-')):
                    if lines[i].startswith('-'):
                        dels.append(lines[i][1:])
                    else:
                        adds.append(lines[i][1:])
                    i += 1
                
                max_len = max(len(dels), len(adds))
                for j in range(max_len):
                    d_text = dels[j] if j < len(dels) else None
                    a_text = adds[j] if j < len(adds) else None
                    
                    c_old_ln = old_ln if d_text is not None else ""
                    c_new_ln = new_ln if a_text is not None else ""
                    
                    if d_text is not None: old_ln += 1
                    if a_text is not None: new_ln += 1
                    
                    t = 'mod'
                    if d_text is None: t = 'add'
                    if a_text is None: t = 'del'
                    
                    files_diffs[current_file].append({
                        'type': t,
                        'old_ln': c_old_ln,
                        'new_ln': c_new_ln,
                        'old_text': d_text if d_text is not None else "",
                        'new_text': a_text if a_text is not None else ""
                    })
            else:
                i += 1
        else:
            i += 1
            
    return files_diffs

def generate_html_diff(diff_text: str, output_file: Path, title: str = "Diff Report") -> None:
    files_diffs = parse_unified_diff(diff_text)
    
    font_path = Path(__file__).parent.parent / 'font' / 'JetBrainsMono-Medium.ttf'
    font_uri = font_path.absolute().as_uri() if font_path.exists() else ""
    
    nav_html = ""
    panels_html = ""
    
    for i, (filename, hunks) in enumerate(files_diffs.items()):
        nav_html += f'<div id="nav-{i}" class="nav-item" onclick="showFile({i})">{escape(filename)}</div>'
        
        ext = filename.split('.')[-1] if '.' in filename else ''
        
        rows_list = []
        for hunk in hunks:
            t = hunk['type']
            if t == 'header':
                rows_list.append(f'<div class="hunk">{escape(hunk["text"])}</div>')
            else:
                old_content = f'<pre><code class="language-{ext}">{escape(hunk.get("old_text", ""))}</code></pre>' if hunk.get("old_text", "") else "&nbsp;"
                new_content = f'<pre><code class="language-{ext}">{escape(hunk.get("new_text", ""))}</code></pre>' if hunk.get("new_text", "") else "&nbsp;"
                
                if t == 'ctx':
                    rows_list.append(f'<div class="num ctx">{hunk["old_ln"]}</div><div class="sign ctx"></div><div class="code ctx">{old_content}</div>')
                    rows_list.append(f'<div class="num ctx">{hunk["new_ln"]}</div><div class="sign ctx"></div><div class="code ctx">{new_content}</div>')
                elif t == 'add':
                    rows_list.append('<div class="num ctx"></div><div class="sign ctx"></div><div class="code ctx">&nbsp;</div>')
                    rows_list.append(f'<div class="num add">{hunk["new_ln"]}</div><div class="sign add">+</div><div class="code add">{new_content}</div>')
                elif t == 'del':
                    rows_list.append(f'<div class="num del">{hunk["old_ln"]}</div><div class="sign del">-</div><div class="code del">{old_content}</div>')
                    rows_list.append('<div class="num ctx"></div><div class="sign ctx"></div><div class="code ctx">&nbsp;</div>')
                elif t == 'mod':
                    rows_list.append(f'<div class="num del">{hunk["old_ln"]}</div><div class="sign del">-</div><div class="code del">{old_content}</div>')
                    rows_list.append(f'<div class="num add">{hunk["new_ln"]}</div><div class="sign add">+</div><div class="code add">{new_content}</div>')

        rows = "".join(rows_list)
        panels_html += f'<div id="panel-{i}" class="panel"><div class="panel-header">{escape(filename)}</div><div class="diff-grid">{rows}</div></div>'

    font_css = f"@font-face {{ font-family: 'JBM'; src: url('{font_uri}'); }}" if font_uri else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{escape(title)}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
<style>
    {font_css}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 0; display: flex; height: 100vh; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #fff; color: #24292f; overflow: hidden; }}
    
    /* 左侧导航栏 */
    nav {{ width: 300px; flex-shrink: 0; background: #f6f8fa; border-right: 1px solid #d0d7de; overflow-y: auto; display: flex; flex-direction: column; }}
    .nav-header {{ flex-shrink: 0; padding: 12px 16px; font-weight: 600; border-bottom: 1px solid #d0d7de; background: #f6f8fa; position: sticky; top: 0; z-index: 10; font-size: 14px; }}
    .nav-item {{ flex-shrink: 0; padding: 8px 16px; cursor: pointer; border-bottom: 1px solid #e1e4e8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 13px; color: #0969da; }}
    .nav-item:hover {{ background: #eaeef2; }}
    .nav-item.active {{ background: #ffffff; font-weight: 600; border-left: 3px solid #fd8c73; color: #24292f; }}
    
    /* 右侧主内容区 */
    main {{ flex: 1; overflow: hidden; background: #ffffff; display: flex; flex-direction: column; position: relative; }}
    
    /* 面板容器需要自带滚动条 */
    .panel {{ display: none; height: 100%; overflow-y: auto; overflow-x: auto; flex-direction: column; }}
    .panel.active {{ display: flex; }}
    
    .panel-header {{ flex-shrink: 0; background: #f6f8fa; padding: 8px 16px; border-bottom: 1px solid #d0d7de; font-family: 'JBM', Consolas, monospace; font-size: 13px; font-weight: 600; position: sticky; top: 0; z-index: 20; }}
    
    /* Diff Grid */
    .diff-grid {{ 
        display: grid; 
        grid-template-columns: 50px 24px 1fr 50px 24px 1fr; 
        font-family: 'JBM', Consolas, monospace; 
        font-size: 12px; 
        width: 100%;
        min-width: 1000px; /* 保证双栏在窄屏下不坍塌 */
    }}
    
    .diff-grid > div {{
        min-height: 20px;
        line-height: 20px;
        background-color: #fff;
        display: flex;
        align-items: flex-start;
    }}
    
    /* 核心修复：提高背景色权重 */
    .diff-grid > .ctx {{ background-color: #ffffff; }}
    .diff-grid > .add {{ background-color: #e6ffec !important; }}
    .diff-grid > .del {{ background-color: #ffebe9 !important; }}
    
    .num {{ color: #6e7781; justify-content: flex-end; padding: 0 8px; user-select: none; border-right: 1px solid #d0d7de; }}
    
    /* 为行号单独设置更深的颜色以示区分 */
    .diff-grid > .num.add {{ background-color: #ccffd8 !important; border-right-color: #bef5cb; }}
    .diff-grid > .num.del {{ background-color: #ffdce0 !important; border-right-color: #fdaeb7; }}
    
    .sign {{ justify-content: center; user-select: none; font-weight: bold; padding: 0; width: 24px; }}
    .sign.add {{ color: #1a7f37; }}
    .sign.del {{ color: #cf222e; }}
    
    .code {{ padding: 0 8px; white-space: pre; /* 改回 pre，保证不折行带来的混乱，启用横向滚动 */ overflow: visible; }}
    
    /* Hunk 头部信息 */
    .hunk {{ 
        background-color: #ddf4ff; 
        color: #0969da; 
        padding: 4px 12px; 
        border-bottom: 1px solid #d0d7de; 
        font-family: -apple-system, sans-serif; 
        font-size: 11px; 
        grid-column: 1 / -1;
        position: sticky;
        left: 0;
    }}
    
    pre {{ margin: 0; padding: 0; display: block; line-height: inherit; font-family: inherit; width: 100%; }}
    code {{ font-family: inherit; margin: 0; padding: 0; display: block; line-height: inherit; }}
    .hljs {{ background: transparent !important; padding: 0 !important; display: inline !important; }}
</style>
</head>
<body>
    <nav>
        <div class="nav-header">Changed Files</div>
        {nav_html}
    </nav>
    <main>
        {panels_html}
    </main>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script>
        function highlightPanel(id) {{
            document.querySelectorAll('#panel-' + id + ' pre code:not(.hljs)').forEach(block => {{
                hljs.highlightElement(block);
            }});
        }}
        
        function showFile(id) {{
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(p => p.classList.remove('active'));
            
            let p = document.getElementById('panel-' + id);
            let n = document.getElementById('nav-' + id);
            
            if(p) p.classList.add('active');
            if(n) n.classList.add('active');
            
            setTimeout(() => highlightPanel(id), 10);
        }}
        
        window.onload = () => {{
            if(document.querySelector('.nav-item')) {{
                showFile(0);
            }}
        }};
    </script>
</body>
</html>"""

    output_file.write_text(html, encoding='utf-8')
