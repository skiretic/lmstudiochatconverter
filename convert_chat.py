import json
from datetime import datetime
import os
import re

def convert_conversation_to_html(input_file, output_file=None):
    """
    Convert a conversation JSON file to an interactive HTML chat interface.
    
    Args:
        input_file (str): Path to the input JSON file
        output_file (str): Optional path to save the HTML output
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Prepare output filename if not provided
    if not output_file:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_chat.html"
    
    # Build content
    content_html = ""
    
    # Add system prompt if exists
    if data.get('systemPrompt'):
        content_html += f"""
        <div class="system-prompt">
            <div class="system-prompt-title">System Prompt</div>
            <div>{data['systemPrompt'].replace('\\n', '<br>')}</div>
        </div>
        """
    
    # Process messages
    for i, message in enumerate(data.get('messages', [])):
        if 'versions' in message and len(message['versions']) > 0:
            version = message['versions'][0]
            role = version.get('role', 'unknown')
            
            # Get timestamp if available
            timestamp = ""
            if 'preprocessed' in version and 'timestamp' in version['preprocessed']:
                ts = datetime.fromtimestamp(version['preprocessed']['timestamp']/1000)
                timestamp = ts.strftime('%Y-%m-%d %H:%M:%S')
            
            # Get content
            content_parts = version.get('content', [])
            message_content = ""
            for part in content_parts:
                if part.get('type') == 'text':
                    message_content = part['text']
            
            # Add message bubble
            content_html += f"""
            <div class="message {role}">
                <div class="message-bubble">
                    <div class="message-header">
                        <span class="message-role">{role.capitalize()}</span>
                        {f'<span class="message-timestamp">{timestamp}</span>' if timestamp else ''}
                    </div>
                    <div>{format_content(message_content)}</div>
            """
            
            # Include reasoning steps and details if present (for assistant messages)
            if role == 'assistant' and 'steps' in version:
                # Collect statistics information first
                stats_html = ""
                tool_calls_html = ""
                
                # Process steps to collect statistics and tool calls
                for step in version['steps']:
                    if 'genInfo' in step and step['genInfo']:
                        gen_info = step['genInfo']
                        stats = gen_info.get('stats', {})
                        
                        if stats:
                            stats_html += f"""
                                    <div class="stats-section">
                                        <div class="stats-title">Model Generation Statistics</div>
                            """
                            
                            stat_items = []
                            if 'stopReason' in stats:
                                stat_items.append(f"Stop Reason: {stats['stopReason']}")
                            if 'tokensPerSecond' in stats:
                                stat_items.append(f"Tokens Per Second: {stats['tokensPerSecond']}")
                            if 'timeToFirstTokenSec' in stats:
                                stat_items.append(f"Time to First Token: {stats['timeToFirstTokenSec']}s")
                            if 'totalTimeSec' in stats:
                                stat_items.append(f"Total Time: {stats['totalTimeSec']}s")
                            if 'promptTokensCount' in stats:
                                stat_items.append(f"Prompt Tokens: {stats['promptTokensCount']}")
                            if 'predictedTokensCount' in stats:
                                stat_items.append(f"Predicted Tokens: {stats['predictedTokensCount']}")
                            if 'totalTokensCount' in stats:
                                stat_items.append(f"Total Tokens: {stats['totalTokensCount']}")
                            
                            # Enhanced statistics - Add 1, 2, 3, 4, 6 and 7 metadata
                            # 3. Model identifier and configuration details
                            model_identifier = gen_info.get('indexedModelIdentifier', 'Unknown')
                            if model_identifier != 'Unknown':
                                # Extract just the model name for cleaner display
                                model_name = model_identifier.split('/')[-1] if '/' in model_identifier else model_identifier
                                stat_items.append(f"Model: {model_name}")
                            
                            # 6. Context length information (from load configuration)
                            if 'loadModelConfig' in gen_info and gen_info['loadModelConfig']:
                                load_config = gen_info['loadModelConfig'].get('fields', [])
                                for field in load_config:
                                    if field.get('key') == 'llm.load.contextLength':
                                        context_length = field.get('value')
                                        stat_items.append(f"Context Length: {context_length}")
                            
                            # 7. Quantization details (from load configuration)
                            quantization_info = []
                            if 'loadModelConfig' in gen_info and gen_info['loadModelConfig']:
                                load_config = gen_info['loadModelConfig'].get('fields', [])
                                for field in load_config:
                                    if field.get('key') == 'llm.load.llama.vCacheQuantizationType':
                                        v_quant = field.get('value', {}).get('value', 'Unknown')
                                        quantization_info.append(f"V Cache Quant: {v_quant}")
                                    elif field.get('key') == 'llm.load.llama.kCacheQuantizationType':
                                        k_quant = field.get('value', {}).get('value', 'Unknown')
                                        quantization_info.append(f"K Cache Quant: {k_quant}")
                            
                            if quantization_info:
                                stat_items.extend(quantization_info)
                            
                            # 2. Memory/CPU thread information (from load configuration)  
                            cpu_threads = None
                            if 'loadModelConfig' in gen_info and gen_info['loadModelConfig']:
                                load_config = gen_info['loadModelConfig'].get('fields', [])
                                for field in load_config:
                                    if field.get('key') == 'llm.load.llama.cpuThreadPoolSize':
                                        cpu_threads = field.get('value')
                                        stat_items.append(f"CPU Threads: {cpu_threads}")
                            
                            # 4. Token efficiency metrics (calculate from tokens)
                            prompt_tokens = stats.get('promptTokensCount', 0)
                            predicted_tokens = stats.get('predictedTokensCount', 0)
                            total_tokens = stats.get('totalTokensCount', 0)
                            
                            if predicted_tokens > 0 and prompt_tokens > 0:
                                # Tokens per prompt token ratio
                                tokens_per_prompt = round(predicted_tokens / prompt_tokens, 2)
                                stat_items.append(f"Tokens/Prompt Token Ratio: {tokens_per_prompt}")
                                
                                # Efficiency (predicted vs total) 
                                if total_tokens > 0:
                                    efficiency = round((predicted_tokens / total_tokens) * 100, 2)
                                    stat_items.append(f"Efficiency: {efficiency}%")
                            
                            for item in stat_items:
                                stats_html += f'<div class="stat-item">{item}</div>'
                            
                            stats_html += "</div>"
                
                # Process tool calls
                if 'tool_calls' in version and version['tool_calls']:
                    tool_calls_html += '<div class="tool-calls">'
                    tool_calls_html += '<div class="tool-call-item"><strong>Tool Calls:</strong></div>'
                    for tool_call in version['tool_calls']:
                        tool_name = tool_call.get('function', {}).get('name', 'Unknown')
                        args = tool_call.get('function', {}).get('arguments', {})
                        tool_calls_html += f'<div class="tool-call-item"><span class="tool-name">{tool_name}</span>: {str(args)}</div>'
                    tool_calls_html += '</div>'
                
                # Add thinking process
                for step in version['steps']:
                    if step.get('type') == 'contentBlock':
                        content = step.get('content', [])
                        for part in content:
                            if part.get('type') == 'text':
                                if 'thinking' in str(step.get('style', {})).lower():
                                    thinking_content = format_content(part['text'])
                                    content_html += f"""
                                    <div class="thinking-process">
                                        <strong>Thinking Process:</strong><br>
                                        {thinking_content}
                                    </div>
                                    """
                
                # Add thinking duration if available
                for step in version['steps']:
                    if 'style' in step and step['style']:
                        style = step['style']
                        if 'title' in style and 'Thought for' in style['title'] and 'seconds' in style['title']:
                            content_html += f"""
                                    <div class="thinking-duration">
                                        {style['title']}
                                    </div>
                                    """
                
                # Add the actual response content from the model
                response_content = ""
                for step in version['steps']:
                    if step.get('type') == 'contentBlock':
                        content = step.get('content', [])
                        for part in content:
                            if part.get('type') == 'text':
                                if 'thinking' not in str(step.get('style', {})).lower():
                                    response_content += f"""
                                    <div class="response-content">
                                        <strong>Model Response:</strong><br>
                                        {format_content(part['text'])}
                                    </div>
                                    """
                
                # Add response content first
                content_html += response_content
                
                # Add statistics and tool calls AFTER the response content
                if stats_html:
                    content_html += stats_html
                
                if tool_calls_html:
                    content_html += tool_calls_html
            
            content_html += "</div></div>"
    
    # Create complete HTML document with light/dark mode toggle
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversation Chat Interface</title>
    <style>
        :root {{
            --bg-color: white;
            --text-color: black;
            --header-bg: #333;
            --header-text: white;
            --message-user-bg: #444;
            --message-user-text: white;
            --message-assistant-bg: #f5f5f5;
            --message-assistant-text: black;
            --message-border: #ddd;
            --system-prompt-bg: #e8e8e8;
            --system-prompt-border: #ccc;
            --thinking-bg: #fff8e1;
            --thinking-border: #ffd54f;
            --stats-bg: #e0e0e0;
            --stats-border: #bdbdbd;
            --tool-calls-bg: #f0f0f0;
            --tool-calls-border: #9e9e9e;
            --response-content-bg: #f0f0f0;
            --response-content-border: #9e9e9e;
            --footer-bg: #f5f5f5;
            --footer-border: #ddd;
            --toggle-bg: #eee;
            --toggle-text: black;
            --code-bg: #f8f8f8;
            --code-border: #ccc;
            --blockquote-bg: #f0f0f0;
            --blockquote-border: #9e9e9e;
        }}

        .dark-mode {{
            --bg-color: #1a1a1a;
            --text-color: #f0f0f0;
            --header-bg: #333;
            --header-text: white;
            --message-user-bg: #444;
            --message-user-text: white;
            --message-assistant-bg: #2d2d2d;
            --message-assistant-text: #f0f0f0;
            --message-border: #555;
            --system-prompt-bg: #3a3a3a;
            --system-prompt-border: #444;
            --thinking-bg: #3e3d39;
            --thinking-border: #6b5b3d;
            --stats-bg: #2a2a2a;
            --stats-border: #555;
            --tool-calls-bg: #3a3a3a;
            --tool-calls-border: #555;
            --response-content-bg: #3a3a3a;
            --response-content-border: #555;
            --footer-bg: #2d2d2d;
            --footer-border: #444;
            --toggle-bg: #333;
            --toggle-text: white;
            --code-bg: #2d2d2d;
            --code-border: #555;
            --blockquote-bg: #2d2d2d;
            --blockquote-border: #555;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
            min-height: 100vh;
            padding: 0;
            margin: 0;
            line-height: 1.6;
        }}
        
        .container {{
            width: 100vw;
            height: 100vh;
            background: var(--bg-color);
            border: none;
            box-shadow: none;
            overflow: auto;
        }}
        
        .header {{
            background-color: var(--header-bg);
            color: var(--header-text);
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid var(--message-border);
            width: 100%;
            position: relative;
        }}
        
        .header h1 {{
            font-size: 1.8rem;
            margin-bottom: 10px;
        }}
        
        .conversation-info {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            font-size: 0.9rem;
        }}
        
        .chat-container {{
            padding: 20px;
            width: 100%;
            height: calc(100vh - 150px);
            overflow-y: auto;
            box-sizing: border-box;
        }}
        
        .message {{
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }}
        
        .message.user {{
            align-items: flex-end;
        }}
        
        .message-bubble {{
            max-width: 80%;
            padding: 15px;
            border: 1px solid var(--message-border);
            position: relative;
            line-height: 1.5;
            word-wrap: break-word;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .user .message-bubble {{
            background-color: var(--message-user-bg);
            color: var(--message-user-text);
            border-bottom-right-radius: 5px;
        }}
        
        .assistant .message-bubble {{
            background-color: var(--message-assistant-bg);
            color: var(--message-assistant-text);
            border: 1px solid var(--message-border);
            border-bottom-left-radius: 5px;
        }}
        
        .message-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            font-size: 0.85rem;
        }}
        
        .message-role {{
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .message-timestamp {{
            font-size: 0.7rem;
            opacity: 0.8;
        }}
        
        .thinking-process {{
            background-color: var(--thinking-bg);
            border-left: 4px solid var(--thinking-border);
            padding: 15px;
            margin: 10px 0;
            font-size: 0.9rem;
            border-radius: 8px;
        }}
        
        .thinking-duration {{
            background-color: var(--toggle-bg);
            color: var(--toggle-text);
            padding: 5px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            margin-top: 5px;
            display: inline-block;
        }}
        
        .stats-section {{
            background-color: var(--stats-bg);
            padding: 15px;
            border: 1px solid var(--stats-border);
            margin: 10px 0;
            font-size: 0.9rem;
            border-radius: 8px;
        }}
        
        .stats-title {{
            font-weight: bold;
            margin-bottom: 8px;
            color: inherit;
        }}
        
        .stat-item {{
            margin: 5px 0;
            padding: 3px 0;
        }}
        
        .tool-calls {{
            background-color: var(--tool-calls-bg);
            padding: 15px;
            border: 1px solid var(--tool-calls-border);
            margin: 10px 0;
            font-size: 0.9rem;
            border-radius: 8px;
        }}
        
        .tool-call-item {{
            margin: 8px 0;
            padding: 5px 0;
        }}
        
        .tool-name {{
            font-weight: bold;
            color: inherit;
        }}
        
        .response-content {{
            background-color: var(--response-content-bg);
            border-left: 4px solid var(--response-content-border);
            padding: 15px;
            margin: 10px 0;
            font-size: 0.9rem;
            border-radius: 8px;
        }}
        
        .footer {{
            text-align: center;
            padding: 15px;
            background: var(--footer-bg);
            border-top: 1px solid var(--footer-border);
            font-size: 0.8rem;
            width: 100%;
            position: relative;
        }}
        
        .system-prompt {{
            background-color: var(--system-prompt-bg);
            padding: 15px;
            border: 1px solid var(--system-prompt-border);
            margin: 15px 0;
            font-size: 0.9rem;
            border-radius: 8px;
        }}
        
        .system-prompt-title {{
            font-weight: bold;
            margin-bottom: 8px;
        }}
        
        .theme-toggle {{
            position: absolute;
            top: 20px;
            right: 20px;
            background-color: var(--toggle-bg);
            color: var(--toggle-text);
            border: none;
            border-radius: 20px;
            padding: 8px 16px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .theme-toggle:hover {{
            background-color: var(--message-border);
        }}
        
        .theme-toggle-icon {{
            font-size: 1.2rem;
        }}
        
        /* Enhanced Markdown styling */
        .markdown-content h1,
        .markdown-content h2,
        .markdown-content h3,
        .markdown-content h4,
        .markdown-content h5,
        .markdown-content h6 {{
            margin-top: 1.5em;
            margin-bottom: 0.8em;
            font-weight: bold;
        }}
        
        .markdown-content h1 {{
            font-size: 1.8rem;
        }}
        
        .markdown-content h2 {{
            font-size: 1.5rem;
        }}
        
        .markdown-content h3 {{
            font-size: 1.2rem;
        }}
        
        .markdown-content p {{
            margin-bottom: 0.8em;
        }}
        
        .markdown-content ul,
        .markdown-content ol {{
            margin: 0.8em 0;
            padding-left: 1.5em;
        }}
        
        .markdown-content li {{
            margin-bottom: 0.4em;
        }}
        
        .markdown-content pre {{
            background-color: var(--code-bg);
            border: 1px solid var(--code-border);
            border-radius: 6px;
            padding: 12px;
            overflow-x: auto;
            margin: 1em 0;
            font-size: 0.9rem;
        }}
        
        .markdown-content code {{
            background-color: var(--code-bg);
            border: 1px solid var(--code-border);
            border-radius: 4px;
            padding: 2px 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        .markdown-content blockquote {{
            background-color: var(--blockquote-bg);
            border-left: 4px solid var(--blockquote-border);
            padding: 12px 15px;
            margin: 1em 0;
            font-style: italic;
        }}
        
        .markdown-content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
        }}
        
        .markdown-content th,
        .markdown-content td {{
            border: 1px solid var(--message-border);
            padding: 8px 12px;
            text-align: left;
        }}
        
        .markdown-content th {{
            background-color: var(--stats-bg);
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Conversation Chat Interface</h1>
            <div class="conversation-info">
                <span>Conversation: {data.get('name', 'Unknown Conversation')}</span>
                <span>Created: {datetime.fromtimestamp(data['createdAt']/1000).strftime('%Y-%m-%d %H:%M:%S') if data.get('createdAt') else 'Unknown'}</span>
                <span>Total Tokens: {data.get('tokenCount', 0)}</span>
            </div>
            <button class="theme-toggle" id="themeToggle">
                <span class="theme-toggle-icon" id="themeIcon">🌙</span>
                <span>Toggle Theme</span>
            </button>
        </div>
        
        <div class="chat-container" id="chatContainer">
            {content_html}
        </div>
        
        <div class="footer">
            <p>Generated by LM Studio Chat Parser</p>
        </div>
    </div>

    <script>
        // Check for saved theme preference or respect system preference
        function checkThemePreference() {{
            const savedTheme = localStorage.getItem('theme');
            const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
            
            if (savedTheme) {{
                document.body.classList.toggle('dark-mode', savedTheme === 'dark');
                updateThemeIcon(savedTheme === 'dark');
            }} else if (prefersDarkScheme.matches) {{
                document.body.classList.add('dark-mode');
                updateThemeIcon(true);
            }}
        }}
        
        // Update theme icon based on current mode
        function updateThemeIcon(isDarkMode) {{
            const icon = document.getElementById('themeIcon');
            icon.textContent = isDarkMode ? '☀️' : '🌙';
        }}
        
        // Toggle theme
        function toggleTheme() {{
            document.body.classList.toggle('dark-mode');
            const isDarkMode = document.body.classList.contains('dark-mode');
            localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
            updateThemeIcon(isDarkMode);
        }}
        
        // Initialize theme on page load
        document.addEventListener('DOMContentLoaded', function() {{
            checkThemePreference();
            document.getElementById('themeToggle').addEventListener('click', toggleTheme);
        }});
    </script>
</body>
</html>"""
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML chat interface saved to {output_file}")

def format_content(content):
    """Format content with enhanced Markdown support."""
    if not content:
        return ""
    
    # Convert markdown-style elements
    formatted = content
    
    # Handle code blocks (multi-line)
    formatted = re.sub(r'```([\s\S]*?)```', r'<pre><code>\1</code></pre>', formatted)
    
    # Handle inline code 
    formatted = re.sub(r'`([^`]+)`', r'<code>\1</code>', formatted)
    
    # Handle headers (# Header)
    formatted = re.sub(r'^#{1,6}\s+(.*)$', r'<h3>\1</h3>', formatted, flags=re.MULTILINE)
    
    # Handle bold text (**bold** or __bold__)
    formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted)
    formatted = re.sub(r'__(.*?)__', r'<strong>\1</strong>', formatted)
    
    # Handle italic text (*italic* or _italic_)
    formatted = re.sub(r'\*(.*?)\*', r'<em>\1</em>', formatted)
    formatted = re.sub(r'_(.*?)_', r'<em>\1</em>', formatted)
    
    # Handle strikethrough
    formatted = re.sub(r'~~(.*?)~~', r'<del>\1</del>', formatted)
    
    # Handle bullet lists (starting with - or *)
    lines = formatted.split('\n')
    in_list = False
    for i, line in enumerate(lines):
        if line.strip().startswith(('- ', '* ')):
            if not in_list:
                lines[i] = '<ul><li>' + line[2:].strip() + '</li>'
                in_list = True
            else:
                lines[i] = '<li>' + line[2:].strip() + '</li>'
        elif in_list and line.strip():
            # Check if this is a new list item or continuation of previous 
            if not line.startswith('- ') and not line.startswith('* '):
                lines[i-1] += '</ul><p>' + line
                in_list = False
            else:
                lines[i] = '<li>' + line[2:].strip() + '</li>'
        elif in_list:
            # End of list if we encounter a blank line or non-list item
            if not line.strip():
                lines[i-1] += '</ul>'
                in_list = False
    
    formatted = '\n'.join(lines)
    
    # Handle blockquotes (lines starting with >)
    formatted = re.sub(r'^>\s+(.*)$', r'<blockquote>\1</blockquote>', formatted, flags=re.MULTILINE)
    
    # Convert new lines to <br> tags
    formatted = formatted.replace('\n\n', '</p><p>').replace('\n', '<br>')
    
    # Add paragraph tags around content
    if not formatted.startswith('<'):
        formatted = f'<p>{formatted}</p>'
    
    return formatted

# Usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 convert_chat_html.py <input_file.json> [output_file.html]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_conversation_to_html(input_file, output_file)
