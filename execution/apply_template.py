#!/usr/bin/env python3
"""
Applies design template to CV and cover letter, generates final PDFs.
Converts markdown to styled PDF matching the template design.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import json
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import PyPDF2

def load_markdown(file_path):
    """Load markdown file."""
    with open(file_path, 'r') as f:
        return f.read()

def load_json(file_path):
    """Load JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def analyze_template_style(template_path):
    """
    Analyze the design template PDF to extract style information.
    This is a placeholder - in practice, you'd extract fonts, colors, etc.
    """
    # For now, return default professional styling
    # TODO: Implement actual template analysis using PDF parsing or Claude vision
    return {
        'font_family': 'Arial, sans-serif',
        'heading_color': '#2c3e50',
        'text_color': '#333333',
        'accent_color': '#3498db',
        'font_size_body': '11pt',
        'font_size_heading': '24pt',
        'font_size_subheading': '16pt',
        'line_height': '1.6',
        'margin': '0.75in'
    }

def create_css(style_config):
    """Generate CSS based on style configuration."""
    return f"""
    @page {{
        size: A4;
        margin: {style_config['margin']};
    }}

    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}

    body {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: {style_config['font_size_body']};
        color: {style_config['text_color']};
        line-height: {style_config['line_height']};
    }}

    h1 {{
        font-size: {style_config['font_size_heading']};
        color: {style_config['heading_color']};
        font-weight: 700;
        letter-spacing: 0;
        margin-bottom: 0.3em;
        margin-top: 0;
    }}

    h1, h2, h3, p {{
        font-variant-numeric: normal;
    }}

    h2 {{
        font-size: {style_config['font_size_subheading']};
        color: {style_config['heading_color']};
        font-weight: 600;
        border-bottom: 2px solid {style_config['accent_color']};
        padding-bottom: 0.2em;
        margin-top: 1em;
        margin-bottom: 0.5em;
    }}

    h3 {{
        font-size: {style_config['font_size_body']};
        color: {style_config['heading_color']};
        margin-top: 0.8em;
        margin-bottom: 0.3em;
        font-weight: bold;
    }}

    p {{
        margin: 0.3em 0;
    }}

    ul {{
        margin: 0.3em 0;
        padding-left: 1.5em;
    }}

    li {{
        margin: 0.2em 0;
    }}

    strong {{
        color: {style_config['heading_color']};
    }}

    a {{
        color: {style_config['accent_color']};
        text-decoration: none;
    }}

    hr {{
        border: none;
        border-top: 1px solid #ddd;
        margin: 1em 0;
    }}
    """

def markdown_to_pdf(markdown_content, output_path, style_config):
    """Convert markdown to styled PDF."""
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content, extensions=['extra', 'nl2br'])

    # Wrap in HTML structure
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            {create_css(style_config)}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Convert to PDF
    font_config = FontConfiguration()
    html = HTML(string=full_html)
    html.write_pdf(output_path, font_config=font_config)

def generate_filename(job_analysis, doc_type):
    """Generate filename based on job and date."""
    date_str = datetime.now().strftime('%Y%m%d')
    job_title = (job_analysis.get('job_title') or 'Job').replace(' ', '_').replace('/', '_')
    company = (job_analysis.get('company') or 'Company').replace(' ', '_').replace('/', '_')

    # Sanitize filename
    job_title = ''.join(c for c in job_title if c.isalnum() or c in ['_', '-'])
    company = ''.join(c for c in company if c.isalnum() or c in ['_', '-'])

    return f"{doc_type}_{company}_{job_title}_{date_str}.pdf"

def main():
    parser = argparse.ArgumentParser(description='Apply template and generate PDFs')
    parser.add_argument('--cv', default='.tmp/job_applications/tailored_cv.md',
                       help='Path to tailored CV markdown')
    parser.add_argument('--cover-letter', default='.tmp/job_applications/cover_letter.md',
                       help='Path to cover letter markdown')
    parser.add_argument('--template', default='resources/job_applications/cv_template.pdf',
                       help='Path to design template PDF')
    parser.add_argument('--job-analysis', default='.tmp/job_applications/job_analysis.json',
                       help='Path to job analysis (for filename generation)')
    parser.add_argument('--output-dir', default='.tmp/job_applications',
                       help='Output directory for PDFs')
    parser.add_argument('--skip-cover-letter', action='store_true',
                       help='Skip cover letter generation')

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load job analysis for filename
    job_analysis = {}
    if Path(args.job_analysis).exists():
        job_analysis = load_json(args.job_analysis)

    # Analyze template if it exists
    style_config = {}
    template_path = Path(args.template)
    if template_path.exists():
        print(f"Analyzing design template: {template_path}")
        style_config = analyze_template_style(template_path)
    else:
        print("No template found, using default professional styling")
        style_config = analyze_template_style(None)

    # Generate CV PDF
    cv_path = Path(args.cv)
    if cv_path.exists():
        print(f"Converting CV to PDF...")
        cv_content = load_markdown(cv_path)

        cv_filename = generate_filename(job_analysis, 'CV')
        cv_output = output_dir / cv_filename

        markdown_to_pdf(cv_content, cv_output, style_config)
        print(f"✓ CV saved to: {cv_output}")
    else:
        print(f"Warning: CV not found at {cv_path}", file=sys.stderr)

    # Generate cover letter PDF
    if not args.skip_cover_letter:
        cl_path = Path(args.cover_letter)
        if cl_path.exists():
            print(f"Converting cover letter to PDF...")
            cl_content = load_markdown(cl_path)

            cl_filename = generate_filename(job_analysis, 'CoverLetter')
            cl_output = output_dir / cl_filename

            markdown_to_pdf(cl_content, cl_output, style_config)
            print(f"✓ Cover letter saved to: {cl_output}")
        else:
            print(f"Warning: Cover letter not found at {cl_path}", file=sys.stderr)

    print(f"\n✓ All documents generated in: {output_dir}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
