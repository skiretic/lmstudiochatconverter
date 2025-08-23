import json
from datetime import datetime
import os

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
                    message_content = part['text'].replace('\n', '<br>')
            
            # Add message bubble
            content_html += f"""
            <div class="message {role}">
                <div class="message-bubble">
                    <div class="message-header">
                        <span class="message-role">{role.capitalize()}</span>
                        {f'<span class="message-timestamp">{timestamp}</span>' if timestamp else ''}
                    </div>
                    <div>{message_content}</div>
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
                                    content_html += f"""
                                    <div class="thinking-process">
                                        <strong>Thinking Process:</strong><br>
                                        {part['text'].replace('\n', '<br>')}
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
                                        {part['text'].replace('\n', '<br>')}
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
            --header-bg: black;
            --header-text: white;
            --message-user-bg: black;
            --message-user-text: white;
            --message-assistant-bg: white;
            --message-assistant-text: black;
            --message-border: black;
            --system-prompt-bg: #f0f0f0;
            --system-prompt-border: black;
            --thinking-bg: #f0f0f0;
            --thinking-border: black;
            --stats-bg: #f0f0f0;
            --stats-border: black;
            --tool-calls-bg: #f0f0f0;
            --tool-calls-border: black;
            --response-content-bg: #e8f4f8;
            --response-content-border: #b3e0ff;
            --footer-bg: #f0f0f0;
            --footer-border: black;
            --toggle-bg: #f0f0f0;
            --toggle-text: black;
        }}

        .dark-mode {{
            --bg-color: #1a1a1a;
            --text-color: #e0e0e0;
            --header-bg: #000000;
            --header-text: #ffffff;
            --message-user-bg: #000000;
            --message-user-text: #ffffff;
            --message-assistant-bg: #2d2d2d;
            --message-assistant-text: #e0e0e0;
            --message-border: #404040;
            --system-prompt-bg: #2d2d2d;
            --system-prompt-border: #404040;
            --thinking-bg: #252525;
            --thinking-border: #404040;
            --stats-bg: #252525;
            --stats-border: #404040;
            --tool-calls-bg: #252525;
            --tool-calls-border: #404040;
            --response-content-bg: #1e3a4d;
            --response-content-border: #1c3d5a;
            --footer-bg: #252525;
            --footer-border: #404040;
            --toggle-bg: #333333;
            --toggle-text: #ffffff;
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
        }}
        
        .thinking-process {{
            background-color: var(--thinking-bg);
            border-left: 4px solid var(--message-border);
            padding: 12px;
            margin: 10px 0;
            font-size: 0.9rem;
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
            padding: 10px;
            border: 1px solid var(--stats-border);
            margin: 10px 0;
            font-size: 0.8rem;
        }}
        
        .stats-title {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-item {{
            margin: 3px 0;
        }}
        
        .tool-calls {{
            background-color: var(--tool-calls-bg);
            padding: 10px;
            border: 1px solid var(--tool-calls-border);
            margin: 10px 0;
            font-size: 0.9rem;
        }}
        
        .tool-call-item {{
            margin: 5px 0;
        }}
        
        .tool-name {{
            font-weight: bold;
        }}
        
        .response-content {{
            background-color: var(--thinking-bg);
            border-left: 4px solid var(--message-border);
            padding: 12px;
            margin: 10px 0;
            font-size: 0.9rem;
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

# Usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 convert_chat_html.py <input_file.json> [output_file.html]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_conversation_to_html(input_file, output_file)
