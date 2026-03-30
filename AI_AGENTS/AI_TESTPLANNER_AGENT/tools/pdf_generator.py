import os
from markdown_pdf import MarkdownPdf, Section

def generate_pdf(llm_output: str, output_path: str):
    """
    Generates a PDF directly from the AI-generated Markdown text.
    """
    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(Section(llm_output))
    pdf.save(output_path)
    return True
