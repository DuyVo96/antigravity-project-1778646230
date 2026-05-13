import json
import os
import re
import sys
from pathlib import Path

def load_config():
    if not os.path.exists("config.json"):
        raise FileNotFoundError("config.json not found. Please ensure it exists in the project root.")
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def validate_content_format(content):
    if not content or not content.strip():
        raise ValueError("Content is empty")
    
    # Check for double newlines (paragraph separators)
    if '\n\n' not in content:
        raise ValueError("Content must have at least 2 paragraphs separated by blank lines (double newline)")
    
    # Split by double newlines
    paragraphs = re.split(r'\n\s*\n', content.strip())
    
    if len(paragraphs) < 2:
        raise ValueError(f"Need at least 2 paragraphs, found {len(paragraphs)}")
    
    # Validate each paragraph has some content
    for i, para in enumerate(paragraphs):
        if not para.strip():
            raise ValueError(f"Paragraph {i+1} is empty")
        lines = para.strip().split('\n')
        if not any(line.strip() for line in lines):
            raise ValueError(f"Paragraph {i+1} has no valid text lines")
    
    return paragraphs

def main():
    try:
        config = load_config()
        content_file = config['paths']['content_file']
        config_file = config['paths']['config_file']
        default_size = config['text']['default_size']
        
        # 1. Check if content.txt exists
        if not os.path.exists(content_file):
            print(f"⚠️  Creating sample {content_file}...")
            sample = "You don't lack motivation\nYou lack discipline\n\nDiscipline is what strong women build\nwhen motivation disappears\n\nBuild discipline\nBecome the unstoppable woman you admire"
            with open(content_file, "w", encoding="utf-8") as f:
                f.write(sample)
            print(f"✏️  Created sample {content_file}. Edit it and run again!")
            sys.exit(0)
        
        # 2. Read and validate content
        with open(content_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        try:
            paragraphs = validate_content_format(content)
        except ValueError as e:
            print(f"❌ Content validation failed: {e}")
            print(f"\n💡 Tips:")
            print(f"  - Separate each slide with a blank line (double newline)")
            print(f"  - Each paragraph becomes one slide")
            print(f"  - Lines within a paragraph are separate text layers on that slide")
            sys.exit(1)
        
        # 3. Convert paragraphs to slides
        json_output = []
        for i, para_text in enumerate(paragraphs):
            lines_text = para_text.strip().split("\n")
            lines = []
            for text in lines_text:
                if text.strip():
                    lines.append({
                        "text": text.strip(),
                        "size": default_size
                    })
            
            json_output.append({
                "imagePath": f"./{config['paths']['images_dir']}/{config['niche']}/image_{i+1:03d}.jpg",
                "lines": lines
            })
        
        # 4. Save JSON
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(json_output, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Success! Parsed {len(json_output)} slides into {config_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
