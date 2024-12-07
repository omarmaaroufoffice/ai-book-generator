import os
from pathlib import Path
from fpdf import FPDF
from openai import OpenAI
from dotenv import load_dotenv
import json
from PyPDF2 import PdfMerger

# Load environment variables from .env file
load_dotenv()

class BookGenerator:
    def __init__(self, topic, api_key):
        self.topic = topic
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        self.temperature = 0.7
        self.book_dir = None
        self.title = None
        
    def generate_text(self, prompt):
        """Generate text using OpenAI API"""
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a professional book writer and editor."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
        )
        return completion.choices[0].message.content.strip()

    def create_chapter_outline(self, chapter_title):
        """Generate detailed markdown outline for a chapter"""
        print(f"\nGenerating outline for chapter: {chapter_title}")
        outline_prompt = f"""
        Create a detailed markdown outline for the chapter "{chapter_title}" in a book about {self.topic}.
        Include:
        - Main points to be covered
        - Subtopics and their key elements
        - Examples and case studies to be included
        - Key takeaways
        
        Format in proper markdown with headers, bullet points, and nested lists.
        """
        return self.generate_text(outline_prompt)

    def clean_chapter_content(self, content):
        """Clean and improve chapter content"""
        print("Cleaning and improving chapter content...")
        cleaning_prompt = f"""
        Review and improve this book chapter content. Make it:
        1. Flow naturally like a professional book
        2. Remove any AI-like language or artifacts
        3. Ensure consistent tone and style
        4. Fix any grammatical or structural issues
        5. Format section titles properly:
           - Main sections start with ##
           - Subsections start with ###
           - No asterisks or other markdown formatting
           - Keep only essential bullet points
           - Ensure proper paragraph breaks
        
        Content to clean:
        {content}
        """
        return self.generate_text(cleaning_prompt)

    def create_chapter_pdf(self, title, content, chapter_dir):
        """Create PDF for a single chapter with professional formatting"""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Set margins
        pdf.set_margins(25, 25, 25)
        
        def clean_text(text):
            """Clean text of problematic characters"""
            replacements = {
                '"': '"',
                '"': '"',
                ''': "'",
                ''': "'",
                '–': '-',
                '—': '-',
                '…': '...',
                '\u2019': "'",  # Right single quotation mark
                '\u2018': "'",  # Left single quotation mark
                '\u201C': '"',  # Left double quotation mark
                '\u201D': '"',  # Right double quotation mark
                '\u2013': '-',  # En dash
                '\u2014': '-',  # Em dash
                '\u2022': '-',  # Bullet point
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            return text.encode('ascii', 'replace').decode('ascii')
        
        # Chapter title
        pdf.set_font('Helvetica', 'B', 24)
        pdf.cell(0, 20, f"Chapter {clean_text(title)}", ln=True, align='L')
        pdf.ln(10)
        
        # Process content sections
        sections = content.split('\n## ')
        
        for section in sections:
            if section.strip():
                # Handle section titles (## level)
                if '##' in section:
                    parts = section.split('\n', 1)
                    pdf.set_font('Helvetica', 'B', 16)
                    pdf.cell(0, 10, clean_text(parts[0].replace('#', '').strip()), ln=True)
                    pdf.ln(5)
                    content = parts[1] if len(parts) > 1 else ""
                else:
                    content = section
                
                # Handle subsections (### level)
                subsections = content.split('\n### ')
                for subsection in subsections:
                    if subsection.strip():
                        if '###' in subsection:
                            parts = subsection.split('\n', 1)
                            pdf.set_font('Helvetica', 'B', 14)
                            pdf.cell(0, 10, clean_text(parts[0].replace('#', '').strip()), ln=True)
                            pdf.ln(5)
                            text = parts[1] if len(parts) > 1 else ""
                        else:
                            text = subsection
                        
                        # Regular paragraphs
                        pdf.set_font('Helvetica', '', 12)
                        # Clean up markdown artifacts
                        text = clean_text(text)
                        text = text.replace('**', '')
                        text = text.replace('*', '')
                        text = text.replace('####', '')
                        
                        # Process paragraphs
                        paragraphs = text.split('\n')
                        for paragraph in paragraphs:
                            if paragraph.strip():
                                # Handle bullet points
                                if paragraph.strip().startswith('-'):
                                    pdf.ln(5)
                                    pdf.cell(10, 5, '-', ln=0)
                                    pdf.multi_cell(0, 5, clean_text(paragraph.strip()[1:].strip()))
                                    pdf.ln(5)
                                else:
                                    # Regular paragraph
                                    pdf.multi_cell(0, 5, clean_text(paragraph.strip()))
                                    pdf.ln(5)
                
                pdf.ln(10)
        
        # Add page numbers
        pdf.set_auto_page_break(auto=True, margin=15)
        for page in range(1, pdf.page_no() + 1):
            pdf.page = page
            pdf.set_y(-15)
            pdf.set_font('Helvetica', 'I', 8)
            pdf.cell(0, 10, f'Page {page}', align='C')
        
        pdf_path = chapter_dir / f"{title.lower().replace(' ', '_')}.pdf"
        pdf.output(str(pdf_path))
        return pdf_path

    def merge_pdfs(self, pdf_files):
        """Merge all chapter PDFs into one book"""
        print("\nMerging all chapters into final book PDF...")
        merger = PdfMerger()
        for pdf in pdf_files:
            merger.append(str(pdf))
        
        final_pdf_path = self.book_dir / f"{self.title.lower().replace(' ', '_')}_complete.pdf"
        merger.write(str(final_pdf_path))
        merger.close()
        return final_pdf_path

def main():
    # Get API key from environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")
    
    # Get topic from user
    topic = input("Enter the topic of the book: ")
    print("\nInitializing book generation process...")
    
    # Initialize book generator
    generator = BookGenerator(topic, api_key)
    
    # Generate book structure
    print("\nGenerating book structure...")
    structure_prompt = f"""
    Create a book structure for a guide about {topic}. Return ONLY valid JSON in this exact format:
    {{
        "title": "Your Title Here",
        "chapters": [
            {{"title": "Chapter 1 Title", "description": "Chapter 1 description"}},
            {{"title": "Chapter 2 Title", "description": "Chapter 2 description"}},
            {{"title": "Chapter 3 Title", "description": "Chapter 3 description"}}
        ]
    }}
    """
    
    book_structure = generator.generate_text(structure_prompt)
    
    try:
        book_structure = json.loads(book_structure)
    except json.JSONDecodeError:
        print("Error: Could not parse the book structure. Using default structure.")
        book_structure = {
            "title": f"Guide to {topic}",
            "chapters": [
                {"title": "Introduction", "description": "Overview"},
                {"title": "Main Concepts", "description": "Core ideas"},
                {"title": "Applications", "description": "Practical uses"}
            ]
        }
    
    generator.title = book_structure.get('title', f"Guide to {topic}")
    generator.book_dir = Path(generator.title.lower().replace(" ", "_") + "_book")
    generator.book_dir.mkdir(exist_ok=True)
    
    print(f"\nCreating book: {generator.title}")
    print(f"Book directory: {generator.book_dir}")
    
    # Process each chapter
    chapter_pdfs = []
    for i, chapter in enumerate(book_structure['chapters'], 1):
        chapter_title = chapter['title']
        print(f"\n{'='*50}")
        print(f"Processing Chapter {i}: {chapter_title}")
        
        # Create chapter directory
        chapter_dir = generator.book_dir / f"chapter_{i}"
        chapter_dir.mkdir(exist_ok=True)
        
        # Generate and save chapter outline
        outline = generator.create_chapter_outline(chapter_title)
        outline_path = chapter_dir / "outline.md"
        with open(outline_path, 'w') as f:
            f.write(outline)
        print(f"Chapter outline saved to: {outline_path}")
        
        # Generate chapter content using the outline
        print("Generating chapter content...")
        chapter_prompt = f"""
        Write a detailed chapter following this outline:
        {outline}
        
        Requirements:
        - Follow the outline structure exactly
        - Professional book-like tone
        - Clear explanations and examples
        - Smooth transitions between sections
        """
        content = generator.generate_text(chapter_prompt)
        
        # Clean and improve content
        content = generator.clean_chapter_content(content)
        
        # Save raw content
        content_path = chapter_dir / "content.txt"
        with open(content_path, 'w') as f:
            f.write(content)
        print(f"Chapter content saved to: {content_path}")
        
        # Create chapter PDF
        print("Creating chapter PDF...")
        pdf_path = generator.create_chapter_pdf(chapter_title, content, chapter_dir)
        chapter_pdfs.append(pdf_path)
        print(f"Chapter PDF created: {pdf_path}")
    
    # Create final combined PDF
    final_pdf = generator.merge_pdfs(chapter_pdfs)
    print(f"\nFinal book PDF created: {final_pdf}")
    print("\nBook generation complete!")

if __name__ == "__main__":
    main()
