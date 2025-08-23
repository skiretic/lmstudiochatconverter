# LM Studio Chat Converter

A Python script that converts LM Studio conversation JSON files into HTML chat interfaces.

## Description

This script transforms conversation data stored in JSON format (from LM Studio) into a formatted HTML document that displays the conversation as an interactive chat interface. The output includes all conversation metadata, thinking processes, generation statistics, and tool calls in a visually organized layout.

## Features

- **Interactive Chat Interface**: Clean, responsive design that mimics real chat applications
- **Complete Metadata Display**: Shows timestamps, token counts, model information, and system prompts
- **Thinking Process Visualization**: Displays AI reasoning steps with clear separation
- **Generation Statistics**: Shows detailed performance metrics including tokens per second, timing information, and token counts
- **Tool Call Integration**: Visualizes any tool calls made during the conversation
- **Responsive Design**: Works well on different screen sizes
- **Customizable Output**: Generates HTML files ready for web viewing

## Usage
python3 convert_chat.py <input.json> <output.html>

## Input Format
The script expects a JSON file with the following structure:

## Input Format

The script expects a JSON file with the following structure:
- `name`: Conversation name
- `createdAt`: Timestamp of conversation creation
- `tokenCount`: Total tokens in conversation
- `systemPrompt`: System prompt used
- `messages`: Array of message objects with:
  - `versions`: Message versions with content, timestamps, and metadata
  - `role`: Either "user" or "assistant"
  - `content`: Text content of the message
  - For assistant messages: Additional fields like `steps`, `genInfo`, `tool_calls`

## Output

The script generates a complete HTML file with:
- Conversation header showing name, creation date, and token count
- Color-coded user/assistant messages
- Detailed thinking process sections
- Model generation statistics
- Tool call information
- Timestamps for all messages
- Responsive layout that works on desktop and mobile

## Requirements

- Python 3.x
- JSON module (built-in)
- datetime module (built-in)
- os module (built-in)
