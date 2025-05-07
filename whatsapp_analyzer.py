import gradio as gr
import json
import csv
import re
import os
from datetime import datetime

# Function to parse WhatsApp chat text
def parse_whatsapp_chat(chat_text):
    messages = []
    # Regex to match WhatsApp chat format: dd/mm/yy, hh:mm am/pm - sender: message
    pattern = r'(\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2}\s*(?:am|pm)) - ([^:]+): (.*?)(?=\n\d{2}/\d{2}/\d{2},|$|\n\n)'
    
    matches = re.finditer(pattern, chat_text, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        date_time = match.group(1)
        sender = match.group(2).strip()
        message = match.group(3).strip()
        
        # Parse date and time
        try:
            dt = datetime.strptime(date_time, '%d/%m/%y, %I:%M %p')
            formatted_date = dt.strftime('%Y-%m-%d')
            formatted_time = dt.strftime('%H:%M:%S')
        except ValueError:
            formatted_date = date_time.split(',')[0]
            formatted_time = date_time.split(',')[1].strip()
        
        messages.append({
            'date': formatted_date,
            'time': formatted_time,
            'sender': sender,
            'message': message
        })
    
    return messages

# Function to convert parsed messages to JSON
def messages_to_json(messages):
    return json.dumps(messages, indent=2, ensure_ascii=False)

# Function to convert parsed messages to CSV
def messages_to_csv(messages):
    output_file = "whatsapp_chat.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Date', 'Time', 'Sender', 'Message'])
        writer.writeheader()
        writer.writerows(messages)
    return output_file

# Gradio function to handle file upload and processing
def process_whatsapp_chat(file):
    if not file:
        return "Please upload a WhatsApp chat text file.", "", "", None
    
    try:
        # Read the uploaded file
        with open(file.name, 'r', encoding='utf-8') as f:
            chat_text = f.read()
        
        # Parse the chat
        messages = parse_whatsapp_chat(chat_text)
        
        if not messages:
            return "No valid messages found in the chat file.", "", "", None
        
        # Convert to JSON
        json_output = messages_to_json(messages)
        
        # Convert to CSV and get file path
        csv_file = messages_to_csv(messages)
        
        # Read CSV content for display
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        return (
            f"Successfully processed {len(messages)} messages.",
            json_output,
            csv_content,
            csv_file
        )
    
    except Exception as e:
        return f"Error processing file: {str(e)}", "", "", None

# Create Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# WhatsApp Chat Analyzer")
    gr.Markdown("Upload a WhatsApp chat export (.txt) to convert it to JSON and CSV formats.")
    
    with gr.Row():
        file_input = gr.File(label="Upload WhatsApp Chat (.txt)")
    
    with gr.Row():
        process_button = gr.Button("Process Chat")
    
    with gr.Row():
        status_output = gr.Textbox(label="Status")
    
    with gr.Row():
        json_output = gr.Textbox(label="JSON Output", lines=10)
        csv_output = gr.Textbox(label="CSV Output", lines=10)
    
    with gr.Row():
        csv_download = gr.File(label="Download CSV File")
    
    process_button.click(
        fn=process_whatsapp_chat,
        inputs=file_input,
        outputs=[status_output, json_output, csv_output, csv_download]
    )

# Launch the Gradio app
if __name__ == "__main__":
    demo.launch()
