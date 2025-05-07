import gradio as gr
import pandas as pd
import json
import re
import os
from datetime import datetime
import csv
from io import StringIO

def parse_whatsapp_chat(file):
    """
    Parse WhatsApp chat text file into a structured format
    Returns a list of message dictionaries
    """
    messages = []
    # Regular expression to match WhatsApp message format
    # Format example: "22/01/25, 11:59 am - +91 93612 07532: Unable to edit the report..."
    pattern = r'(\d{2}/\d{2}/\d{2},\s\d{1,2}:\d{2}\u202fam|pm\s-\s)(\+\d+\s\d+\s\d+):\s(.+)'
    
    current_message = None
    for line in file:
        line = line.decode('utf-8') if isinstance(line, bytes) else line
        match = re.match(pattern, line)
        
        if match:
            # New message found
            timestamp = match.group(1).strip(' -')
            sender = match.group(2).strip()
            message_text = match.group(3).strip()
            
            try:
                # Parse timestamp
                dt = datetime.strptime(timestamp, '%d/%m/%y, %I:%M%p')
                formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                
                current_message = {
                    'timestamp': formatted_timestamp,
                    'sender': sender,
                    'message': message_text
                }
                messages.append(current_message)
            except ValueError:
                # Skip lines with invalid timestamp format
                continue
        else:
            # Continuation of previous message (multiline)
            if current_message and line.strip():
                current_message['message'] += ' ' + line.strip()
    
    return messages

def convert_to_json(messages):
    """Convert messages to JSON format"""
    return json.dumps(messages, indent=2, ensure_ascii=False)

def convert_to_csv(messages):
    """Convert messages to CSV format"""
    output = StringIO()
    if messages:
        writer = csv.DictWriter(
            output,
            fieldnames=['timestamp', 'sender', 'message'],
            quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()
        for message in messages:
            writer.writerow(message)
    return output.getvalue()

def analyze_chat(file):
    """
    Main function to process uploaded WhatsApp chat file
    Returns JSON and CSV content
    """
    try:
        # Parse the chat file
        messages = parse_whatsapp_chat(file)
        
        if not messages:
            return "Error: No valid messages found in the file.", ""
        
        # Convert to JSON
        json_output = convert_to_json(messages)
        
        # Convert to CSV
        csv_output = convert_to_csv(messages)
        
        # Save files temporarily for download
        json_path = "chat_output.json"
        csv_path = "chat_output.csv"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(json_output)
        
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(csv_output)
        
        return json_path, csv_path
    
    except Exception as e:
        return f"Error processing file: {str(e)}", ""

# Gradio interface
with gr.Blocks(title="WhatsApp Chat Analyzer") as iface:
    gr.Markdown("# WhatsApp Chat Analyzer")
    gr.Markdown("Upload an exported WhatsApp chat text file to convert it to JSON and CSV formats.")
    
    with gr.Row():
        file_input = gr.File(label="Upload WhatsApp Chat (.txt)")
    
    with gr.Row():
        json_output = gr.File(label="Download JSON Output")
        csv_output = gr.File(label="Download CSV Output")
    
    with gr.Row():
        analyze_button = gr.Button("Analyze Chat")
    
    analyze_button.click(
        fn=analyze_chat,
        inputs=[file_input],
        outputs=[json_output, csv_output]
    )

if __name__ == "__main__":
    iface.launch()