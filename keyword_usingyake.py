import gradio as gr
import json
import csv
import re
import os
from datetime import datetime
import yake
import string

# Initialize YAKE keyword extractor with relaxed settings
kw_extractor = yake.KeywordExtractor(n=3, top=15, dedupLim=0.5, stopwords=None)

# Function to extract keywords using YAKE
def extract_keywords(message):
    # Preprocess: lowercase and remove punctuation
    message_cleaned = message.lower().translate(str.maketrans("", "", string.punctuation))
    keywords = kw_extractor.extract_keywords(message_cleaned)
    if keywords:
        keyword_list = [kw[0] for kw in keywords]
        print(f"Keywords for '{message}': {keyword_list}")
        return ", ".join(keyword_list)
    print(f"No keywords for '{message}'")
    return "None"

# Function to parse WhatsApp chat text
async def parse_whatsapp_chat(chat_text):
    messages = []
    # Use user-specified regex with non-breaking space support
    pattern = r'(\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2}\s*(?:am|pm|AM|PM)\s*[\u202F\s]*) - ([^:]+): (.*?)(?=\n\d{2}/\d{2}/\d{2},|$|\n\n)'
    
    if not chat_text.strip():
        print("Chat text is empty.")
        return messages
    
    # Print first 5 lines for debugging
    lines = chat_text.split('\n')
    print("First 5 lines of chat file:")
    for i, line in enumerate(lines[:5]):
        print(f"Line {i+1}: {line}")
    
    matches = re.finditer(pattern, chat_text, re.MULTILINE | re.DOTALL)
    raw_messages = []
    
    for match in matches:
        try:
            date_time = match.group(1).strip()
            sender = match.group(2).strip()
            message = match.group(3).strip()
            
            if message in ["<Media omitted>", "This message was deleted"]:
                continue
            
            print(f"Parsed message: {date_time} - {sender}: {message}")
            raw_messages.append((date_time, sender, message))
        except IndexError:
            continue
    
    # Print unmatched lines
    unmatched_lines = [line.strip() for line in lines if line.strip() and not any(line.strip() in match.group(0) for match in re.finditer(pattern, chat_text))]
    if unmatched_lines:
        print("Unmatched lines (first 5):")
        for i, line in enumerate(unmatched_lines[:5]):
            print(f"Unmatched {i+1}: {line}")
    
    if not raw_messages:
        print("No messages parsed from chat file.")
    
    for date_time, sender, message in raw_messages:
        try:
            # Adjust date format to match DD/MM/YY
            date_formats = [
                '%d/%m/%y, %I:%M %p', '%d/%m/%y, %I:%M%p',
                '%d/%m/%y, %I:%M %p', '%d/%m/%y, %I:%M%p'
            ]
            dt = None
            for fmt in date_formats:
                try:
                    dt = datetime.strptime(date_time, fmt)
                    break
                except ValueError:
                    continue
            if dt is None:
                raise ValueError("Invalid date format")
            formatted_date = dt.strftime('%Y-%m-%d')
            formatted_time = dt.strftime('%H:%M:%S')
        except ValueError:
            formatted_date = date_time.split(',')[0].strip()
            formatted_time = date_time.split(',')[1].strip()
        
        keywords = extract_keywords(message)
        
        messages.append({
            'date': formatted_date,
            'time': formatted_time,
            'sender': sender,
            'message': message,
            'keywords': keywords
        })
    
    return messages

# Function to convert parsed messages to JSON
def messages_to_json(messages):
    return json.dumps(messages, indent=2, ensure_ascii=False)

# Function to convert parsed messages to CSV
def messages_to_csv(messages):
    output_file = "whatsapp_chat.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Date', 'Time', 'Sender', 'Message', 'Keywords'])
        writer.writeheader()
        for msg in messages:
            writer.writerow({
                'Date': msg['date'],
                'Time': msg['time'],
                'Sender': msg['sender'],
                'Message': msg['message'],
                'Keywords': msg['keywords']
            })
    return output_file

# Function to handle file upload and processing
async def process_whatsapp_chat(file):
    if not file:
        return "Please upload a WhatsApp chat text file.", "", "", None
    
    try:
        with open(file.name, 'r', encoding='utf-8-sig') as f:
            chat_text = f.read()
        
        if not chat_text.strip():
            return "Uploaded file is empty.", "", "", None
        
        messages = await parse_whatsapp_chat(chat_text)
        
        if not messages:
            return "No messages parsed from the chat file. Ensure the format is 'DD/MM/YY, H:MM am/pm - Sender: Message'.", "", "", None
        
        json_output = messages_to_json(messages)
        csv_file = messages_to_csv(messages)
        
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
    
    file_input = gr.File(label="Upload WhatsApp Chat (.txt)")
    process_button = gr.Button("Process Chat")
    status_output = gr.Textbox(label="Status", lines=5)
    json_output = gr.Textbox(label="JSON Output", lines=10)
    csv_output = gr.Textbox(label="CSV Output", lines=10)
    csv_download = gr.File(label="Download CSV File")
    
    process_button.click(
        fn=process_whatsapp_chat,
        inputs=file_input,
        outputs=[status_output, json_output, csv_output, csv_download]
    )

# Launch the Gradio app
if __name__ == "__main__":
    demo.launch()
