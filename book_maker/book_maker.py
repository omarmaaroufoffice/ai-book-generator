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
                {"role": "system", "content": "You are a creative and engaging book writer, skilled at adapting your writing style to the topic and audience."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
        )
        return completion.choices[0].message.content.strip()

    def create_chapter_outline(self, chapter_title):
        """Generate detailed markdown outline for a chapter"""
        print(f"\nGenerating outline for chapter: {chapter_title}")
        outline_prompt = f"""
        Create a detailed and engaging outline for the chapter "{chapter_title}" in a book about {self.topic}.
        Consider the narrative flow and reader engagement while including:
        - Key story elements or concepts to cover
        - Natural progression of ideas
        - Engaging subtopics and their development
        - Points where examples or illustrations would be effective
        
        Format in proper markdown with headers, bullet points, and nested lists.
        Make the structure flow naturally and keep the reader engaged throughout.
        """
        return self.generate_text(outline_prompt)

    def clean_chapter_content(self, content):
        """Clean and improve chapter content"""
        print("Cleaning and improving chapter content...")
        cleaning_prompt = f"""
        Review and enhance this chapter content for maximum engagement and clarity. Make it:
        1. Flow naturally with a captivating narrative style
        2. Maintain consistent tone and voice throughout
        3. Use clear, audience-appropriate language
        4. Include smooth transitions between sections
        5. Format properly with:
           - Clear section headings (##)
           - Well-organized subsections (###)
           - Clean formatting without markdown artifacts
           - Natural paragraph breaks
           - Engaging opening and closing for each section
        
        Content to enhance:
        {content}
        """
        return self.generate_text(cleaning_prompt)

    def create_chapter_pdf(self, title, content, chapter_dir):
        """Create PDF for a single chapter with professional formatting"""
        from fpdf import FPDF

        class PDF(FPDF):
            def __init__(self):
                super().__init__()
                self.add_page()
                self.set_auto_page_break(auto=True, margin=15)
                self.set_margins(15, 15, 15)

            def header(self):
                pass

            def footer(self):
                self.set_y(-15)
                self.set_font('Helvetica', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', align='C')

        pdf = PDF()
        
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
                '\u2019': "'",
                '\u2018': "'",
                '\u201C': '"',
                '\u201D': '"',
                '\u2013': '-',
                '\u2014': '-',
                '\u2022': '-',
                '\u2026': '...',
                '\u201c': '"',
                '\u201d': '"',
                '*': '',
                '**': ''
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            
            # Replace any remaining non-ASCII characters
            text = ''.join(char if ord(char) < 128 else '-' for char in text)
            
            # Ensure there's always some space
            text = text.strip()
            if not text:
                return " "
            return text
        
        # Chapter title
        pdf.set_font('Helvetica', 'B', 20)
        pdf.cell(0, 15, f"Chapter: {clean_text(title)}", ln=True, align='L')
        pdf.ln(5)

        # Process content
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            try:
                # Handle headers
                if paragraph.startswith('# '):
                    continue  # Skip chapter title
                elif paragraph.startswith('## '):
                    pdf.set_font('Helvetica', 'B', 14)
                    pdf.ln(5)
                    pdf.multi_cell(0, 6, clean_text(paragraph[3:]))
                    pdf.ln(3)
                elif paragraph.startswith('### '):
                    pdf.set_font('Helvetica', 'B', 12)
                    pdf.ln(4)
                    pdf.multi_cell(0, 6, clean_text(paragraph[4:]))
                    pdf.ln(2)
                elif paragraph.startswith('- '):
                    # Handle bullet points
                    pdf.set_font('Helvetica', '', 10)
                    for line in paragraph.split('\n'):
                        if line.strip():
                            pdf.ln(2)
                            pdf.cell(5, 6, '-', ln=0)
                            pdf.multi_cell(0, 6, clean_text(line[2:]))
                else:
                    # Regular paragraph
                    pdf.set_font('Helvetica', '', 10)
                    cleaned_text = clean_text(paragraph)
                    if cleaned_text.strip():
                        pdf.multi_cell(0, 6, cleaned_text)
                        pdf.ln(3)
            except Exception as e:
                print(f"Warning: Skipping problematic text: {str(e)}")
                continue

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
    Create a complete book structure about {topic}. Consider the scope and complexity of the topic to determine the appropriate number of chapters.
    Return ONLY valid JSON in this format:
    {{
        "title": "An engaging and appropriate title",
        "chapters": [
            {{"title": "Chapter title", "description": "Brief description of chapter content"}},
            // Add as many chapters as needed for comprehensive coverage
        ]
    }}

    Guidelines:
    - Choose an appropriate number of chapters based on the topic
    - Each chapter should have a clear focus and purpose
    - Chapter titles should be engaging and descriptive
    - Ensure logical flow and progression between chapters
    - Consider the target audience when structuring
    """
    
    book_structure = generator.generate_text(structure_prompt)
    
    try:
        book_structure = json.loads(book_structure)
    except json.JSONDecodeError:
        print("Error: Could not parse the book structure. Using default structure.")
        # Make the default structure more flexible
        book_structure = {
            "title": f"Guide to {topic}",
            "chapters": [
                {"title": "Introduction to " + topic, "description": "Overview and fundamentals"},
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
