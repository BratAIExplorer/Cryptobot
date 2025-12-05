import zipfile
import xml.etree.ElementTree as ET
import sys
import os

def read_docx(file_path):
    try:
        with zipfile.ZipFile(file_path) as zf:
            xml_content = zf.read('word/document.xml')
        
        tree = ET.fromstring(xml_content)
        
        # XML namespace for Word documents
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        text_content = []
        for p in tree.findall('.//w:p', namespaces):
            texts = [node.text for node in p.findall('.//w:t', namespaces) if node.text]
            if texts:
                text_content.append(''.join(texts))
            else:
                text_content.append('') # Empty line for paragraph breaks
                
        return '\n'.join(text_content)
    except Exception as e:
        return f"Error reading docx: {str(e)}"

if __name__ == "__main__":
    # Handle the special character in the filename
    # We might need to pass the filename carefully or just hardcode it for this specific task
    # The filename is "🤖 Expert Review.docx"
    
    # Try to find the file in the current directory that ends with "Expert Review.docx"
    # to avoid encoding issues with the robot emoji if passed via command line arguments
    target_file = None
    for f in os.listdir('.'):
        if f.endswith("Expert Review.docx") and not f.startswith("~$"):
            target_file = f
            break
            
    if target_file:
        try:
            content = read_docx(target_file)
            with open('doc_content.txt', 'w', encoding='utf-8') as f:
                f.write("--- CONTENT START ---\n")
                f.write(content)
                f.write("\n--- CONTENT END ---")
            print("Successfully wrote content to doc_content.txt")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Could not find the Expert Review.docx file.")
