#!/usr/bin/env python3
"""
Analyzes master CV PDF and provides structured user data.
Uses hardcoded data extracted from master_cv.pdf - no LLM calls needed.
"""

import json
import sys
import argparse
from pathlib import Path
import PyPDF2
import copy

# Hardcoded user data extracted from master_cv.pdf
# To update: modify this dictionary directly when your CV changes
HARDCODED_USER_DATA = {
    "personal_info": {
        "name": "Jorge González Conde",
        "email": "jorgegoco70@gmail.com",
        "phone": "Not provided",
        "location": "Not explicitly stated (worked in Ourense, España previously, currently remote)",
        "linkedin": "https://www.linkedin.com/in/jorgegoco/",
        "portfolio": "https://jorgegoco.vercel.app/",
        "github": "https://github.com/jorgegoco",
        "website": "https://miagentuca.es/"
    },
    "professional_title": "Desarrollador Python Full Stack",
    "summary": "Desarrollador de software con especialización en Python y desarrollo web full stack. Experiencia en el diseño y consumo de APIs REST, integración de sistemas, y desarrollo de aplicaciones con IA agentica. Capacidad demostrada para crear soluciones innovadoras que mejoran la eficiencia organizacional. Experiencia en mentoría de equipos de 5+ desarrolladores y liderazgo técnico. Comunicador seguro, pensador estratégico y solucionador creativo de problemas que puede desarrollar soluciones de software personalizadas que satisfacen las necesidades organizacionales.",
    "work_experience": [
        {
            "role": "Desarrollador Full Stack Python/Web",
            "company": "Trabajo Freelance",
            "location": "Remoto",
            "start_date": "Septiembre 2022",
            "end_date": "Presente",
            "duration": "2+ años",
            "achievements": [
                "Desarrolló Plataforma de Asistente con IA — Aplicación Python que integra capacidades de IA agéntica con consumo de APIs REST y flujos de trabajo de automatización",
                "Desarrolló endpoints REST personalizados e integración con APIs de OpenAI y Anthropic Claude",
                "Creó littleShop — Sitio web para gestión de pequeñas tiendas con recursos limitados",
                "Desarrolló Sell It — Plataforma de e-commerce completa con gestión de productos, navegación por categorías y panel de administración",
                "Construyó Ticket Admin — Sistema de gestión de tickets para empresas con autenticación, gestión de roles y API REST completa"
            ],
            "skills_used": [
                "Python", "FastAPI", "APIs de IA", "OpenAI API", "Anthropic Claude API",
                "Vite", "React", "TypeScript", "Ruby on Rails", "PostgreSQL", "Redis",
                "MongoDB", "Express", "Node.js", "MERN Stack", "APIs REST"
            ],
            "keywords": ["IA agéntica", "APIs REST", "automatización", "e-commerce", "full stack", "freelance"]
        },
        {
            "role": "Mentor (Voluntario)",
            "company": "Microverse",
            "location": "Remoto",
            "start_date": "Noviembre 2022",
            "end_date": "Presente",
            "duration": "2+ años",
            "achievements": [
                "Proporcionó mentoría a desarrolladores web junior con soporte técnico mediante revisiones de código",
                "Arquitectó mejoras en organización de código mejorando la calidad del código y el rendimiento general en varios proyectos",
                "Trabajó con equipos de 3+ desarrolladores, resultando en una mejora del 15% en la calidad y eficiencia del proyecto",
                "Asesoró sobre cómo mantener la motivación en proyectos full-stack complejos",
                "Logró un aumento del 50% en tareas completadas y 100% de feedback positivo del equipo"
            ],
            "skills_used": ["Mentoría", "Revisiones de código", "Arquitectura de software", "Liderazgo técnico", "Trabajo en equipo"],
            "keywords": ["mentoría", "código review", "mejora de calidad", "liderazgo", "voluntario"]
        },
        {
            "role": "Desarrollador Full Stack Web",
            "company": "The Ticket Merchant",
            "location": "Remoto",
            "start_date": "Octubre 2023",
            "end_date": "Septiembre 2024",
            "duration": "1 año",
            "achievements": [
                "Desarrolló aplicación web interna usando Next.js, servidor Node.js e instancias de SQL Server",
                "Colaboró con miembros del equipo para diseñar e implementar nuevas funcionalidades",
                "Realizó revisiones de código y proporcionó feedback para asegurar calidad del código y mejores prácticas",
                "Asistió en resolución de problemas técnicos y troubleshooting"
            ],
            "skills_used": ["Next.js", "Node.js", "SQL Server", "Material UI", "Code review", "Trabajo en equipo", "Troubleshooting"],
            "keywords": ["aplicación web interna", "full stack", "colaboración", "calidad de código"]
        },
        {
            "role": "Responsable de Producción",
            "company": "MAI",
            "location": "Ourense, España",
            "start_date": "Junio 2002",
            "end_date": "Marzo 2017",
            "duration": "15 años",
            "achievements": [
                "Implementó métodos Six Sigma para optimizar flujos de trabajo, resultando en un aumento del 25% en productividad y reducción del 15% en desperdicios",
                "Gestionó 20+ empleados, mejorando el cumplimiento de seguridad en un 30% y reduciendo errores de inventario en un 20%",
                "Colaboró con equipos multifuncionales para coordinar calendarios de producción y estándares de calidad",
                "Negoció con proveedores para asegurar precios óptimos y términos de entrega"
            ],
            "skills_used": ["Six Sigma", "Gestión de equipos", "Optimización de procesos", "Gestión de inventario", "Negociación", "Control de calidad", "Seguridad"],
            "keywords": ["producción", "Six Sigma", "gestión", "liderazgo", "optimización", "mejora continua"]
        }
    ],
    "education": [
        {
            "degree": "Programa de Desarrollo Web Full Stack Remoto, Tiempo Completo",
            "institution": "Microverse",
            "location": "Remoto",
            "start_date": "Septiembre 2022",
            "end_date": "Presente",
            "gpa": "Not mentioned",
            "honors": "Not mentioned",
            "relevant_coursework": [
                "Algoritmos", "Estructuras de datos", "Desarrollo full-stack", "Ruby", "Rails",
                "JavaScript", "React", "Redux", "Pair programming remoto", "GitHub",
                "Git-flow estándar de la industria", "Standups diarios"
            ],
            "additional_info": "1300+ horas de formación"
        },
        {
            "degree": "Computer Science, Mathematics & AI/ML Specializations",
            "institution": "Coursera, edX, MITx, Stanford Online, Udemy",
            "location": "Online",
            "start_date": "Septiembre 2016",
            "end_date": "Febrero 2021",
            "gpa": "Not mentioned",
            "honors": "Multiple specializations completed",
            "relevant_coursework": [
                "Machine Learning (Stanford)", "Deep Learning Specialization (DeepLearning.AI)",
                "TensorFlow Developer Specialization", "TensorFlow: Data and Deployment",
                "Natural Language Processing Specialization", "Computer Vision",
                "AI for Medicine Specialization", "Mathematics for Machine Learning",
                "MITx: Machine Learning with Python", "MITx: Fundamentals of Statistics",
                "MITx: Probability - The Science of Uncertainty and Data",
                "Java Programming Specializations (Duke, UC San Diego)",
                "Python for Everybody", "Google IT Automation with Python",
                "Machine Learning A-Z: Python & R"
            ],
            "additional_info": "30+ certifications from Stanford, MIT, Google, DeepLearning.AI, and top universities"
        },
        {
            "degree": "Ingeniería Electrónica Industrial y Automática, Tiempo Completo",
            "institution": "Universidad de Vigo",
            "location": "Vigo, España",
            "start_date": "Septiembre 1998",
            "end_date": "Junio 2002",
            "gpa": "Not mentioned",
            "honors": "Not mentioned",
            "relevant_coursework": [
                "Fundamentos de electrónica", "Automatización", "Robótica", "Sistemas de control",
                "Instrumentación", "PLCs", "Microcontroladores", "Sensores", "Actuadores", "Herramientas de software"
            ]
        }
    ],
    "technical_skills": {
        "programming_languages": [
            "Python", "TypeScript", "JavaScript", "Ruby", "Node.js",
            "Java", "C#", "R", "SQL", "GNU Octave"
        ],
        "frameworks": [
            "FastAPI", "Django", "Ruby on Rails", "React", "Redux", "Next.js",
            "Express", "jQuery", "Redux.js", "Material UI"
        ],
        "tools": [
            "Git", "GitHub", "Jest", "pytest", "TDD", "Jira", "Vite",
            "Docker", "Linux"
        ],
        "databases": ["PostgreSQL", "MongoDB", "SQL Server", "Redis", "MySQL"],
        "cloud": ["AWS S3", "AWS Lambda", "Amazon Web Services (AWS)", "Fly.io"],
        "frontend_technologies": ["HTML5", "CSS3", "Responsive Web Design"],
        "apis": ["Diseño e integración de APIs REST", "OpenAI API", "Anthropic Claude API"],
        "ai_ml": [
            "TensorFlow", "TensorFlow.js", "Keras", "PyTorch",
            "Hugging Face Transformers",
            "Machine Learning", "Deep Learning", "Neural Networks",
            "Natural Language Processing (NLP)", "Computer Vision",
            "Workflows de IA Agéntica", "LangChain",
            "RAG (Retrieval-Augmented Generation)", "Vector Databases", "Embeddings",
            "Data Science", "Data Analytics", "Statistics",
            "AI for Medicine"
        ],
        "data_visualization": ["matplotlib", "R Programming", "Data Visualization"],
        "methodologies": ["Six Sigma", "TDD", "Agile Methodologies", "Scrum", "Kanban"],
        "other": ["MERN Stack", "Object-Oriented Programming (OOP)"]
    },
    "soft_skills": [
        "Pair-Programming Remoto", "Trabajo en Equipo", "Mentoría", "Liderazgo técnico",
        "Comunicación", "Pensamiento estratégico", "Resolución creativa de problemas",
        "Gestión de equipos", "Colaboración multifuncional", "Negociación", "Troubleshooting",
        "Code review", "Leadership", "Teamwork", "Collaboration", "Time Management",
        "Project Management", "Remote Work"
    ],
    "languages": [
        {"language": "Español", "proficiency": "Native"},
        {"language": "Inglés", "proficiency": "Professional"}
    ],
    "certifications": [
        # Microverse Certifications
        {"name": "Microverse Full Stack Capstone", "issuer": "Microverse", "date": "Apr 2023"},
        {"name": "Microverse Ruby on Rails Module", "issuer": "Microverse", "date": "Apr 2023"},
        {"name": "Microverse Ruby/Databases Module", "issuer": "Microverse", "date": "Feb 2023"},
        {"name": "Microverse React & Redux Module", "issuer": "Microverse", "date": "Jan 2023", "credential_id": "66351715"},
        {"name": "Microverse JavaScript Module", "issuer": "Microverse", "date": "Nov 2022", "credential_id": "66383605"},
        {"name": "Microverse HTML/CSS Module", "issuer": "Microverse", "date": "Oct 2022"},
        # Google Certifications
        {"name": "Google IT Automation with Python Specialization", "issuer": "Coursera", "date": "Feb 2021", "credential_id": "5Y9R94XBBYVD"},
        {"name": "Google IT Support Specialization", "issuer": "Coursera", "date": "Sep 2020", "credential_id": "NJFGWQ89YRC6"},
        # AI/ML Specializations
        {"name": "Natural Language Processing Specialization", "issuer": "Coursera", "date": "Nov 2020", "credential_id": "T658TQ3PB4C3"},
        {"name": "AI for Medicine Specialization", "issuer": "Coursera", "date": "Jun 2020", "credential_id": "33QNZVS3AQQC"},
        {"name": "TensorFlow: Data and Deployment Specialization", "issuer": "Coursera", "date": "Mar 2020", "credential_id": "7FCHQC77USGY"},
        {"name": "DeepLearning.AI TensorFlow Developer Specialization", "issuer": "Coursera", "date": "Jan 2020", "credential_id": "AJHW4MCSM6XV"},
        {"name": "Deep Learning Specialization", "issuer": "Coursera", "date": "Feb 2018", "credential_id": "UYE57N2B3X6J"},
        {"name": "Mathematics for Machine Learning Specialization", "issuer": "Coursera", "date": "Jun 2018", "credential_id": "RMTLAPKHAZP4"},
        {"name": "Machine Learning", "issuer": "Stanford University (Coursera)", "date": "Apr 2017", "credential_id": "VRLFE95CVHWY"},
        {"name": "Machine Learning A-Z: Hands-On Python & R In Data Science", "issuer": "Udemy", "date": "Jul 2017", "credential_id": "UC-NLDZY48K"},
        # MITx Certifications
        {"name": "Data Analysis in Social Science-Assessing Your Knowledge", "issuer": "MITx", "date": "Dec 2019", "credential_id": "f2f5395f1c6c4661b1fffc7cc0231ade"},
        {"name": "Machine Learning with Python-From Linear Models to Deep Learning", "issuer": "MITx", "date": "Sep 2019", "credential_id": "66dc0f8c2771499fb4e02351dfe013c8"},
        {"name": "Fundamentals of Statistics", "issuer": "MITx", "date": "Jun 2019", "credential_id": "9c545c5c881146448e16b5f02789ea0a"},
        {"name": "Probability - The Science of Uncertainty and Data", "issuer": "MITx", "date": "Jan 2019", "credential_id": "f4b795b5d62945259a36649631e17ea8"},
        # Other Technical Certifications
        {"name": "The Unix Workbench", "issuer": "The Johns Hopkins University", "date": "Jun 2020", "credential_id": "KCDHCZ3QDC9L"},
        {"name": "Python for Everybody Specialization", "issuer": "Coursera", "date": "Sep 2017", "credential_id": "64SVH22AMSBY"},
        {"name": "Learning How to Learn", "issuer": "McMaster University", "date": "Sep 2017", "credential_id": "K5UPPLLZ66JF"},
        # Java Certifications (UC San Diego & Duke)
        {"name": "Mastering the Software Engineering Interview", "issuer": "UC San Diego (Coursera)", "date": "Mar 2017", "credential_id": "C5DATF86W7FS"},
        {"name": "Advanced Data Structures in Java", "issuer": "UC San Diego (Coursera)", "date": "Feb 2017", "credential_id": "E9FC2TQKW8FX"},
        {"name": "Data Structures and Performance", "issuer": "UC San Diego (Coursera)", "date": "Jan 2017", "credential_id": "XP4JBAKGRP27"},
        {"name": "Object Oriented Programming in Java", "issuer": "UC San Diego (Coursera)", "date": "Jan 2017", "credential_id": "RGMKJ6ZRXDPZ"},
        {"name": "Java Programming: Build a Recommendation System", "issuer": "Duke University (Coursera)", "date": "Nov 2016", "credential_id": "FLL8EUSHGP3N"},
        {"name": "Java Programming: Principles of Software Design", "issuer": "Duke University (Coursera)", "date": "Nov 2016", "credential_id": "2W3QQLW6MHTN"},
        {"name": "Java Programming and Software Engineering Fundamentals", "issuer": "Duke University (Coursera)", "date": "Nov 2016", "credential_id": "X9RDB5J8US5D"},
        {"name": "Java Programming: Arrays, Lists, and Structured Data", "issuer": "Duke University (Coursera)", "date": "Oct 2016", "credential_id": "YVYUGVPZ8Y6E"},
        {"name": "Java Programming: Solving Problems with Software", "issuer": "Duke University (Coursera)", "date": "Sep 2016", "credential_id": "RLWNWZULS3LD"},
        {"name": "Programming Foundations with JavaScript, HTML and CSS", "issuer": "Duke University (Coursera)", "date": "Sep 2016", "credential_id": "TE3KACVA44Y6"},
        # LinkedIn Skill Assessments Passed
        {"name": "LinkedIn Skill Assessment: AWS", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: MongoDB", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: C#", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: Git", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: Front-End Development", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: MySQL", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: REST APIs", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: HTML", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: OOP", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: Node.js", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: Agile Methodologies", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: Ruby on Rails", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: Linux", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: Python", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: React.js", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: JavaScript", "issuer": "LinkedIn", "date": "Passed"},
        {"name": "LinkedIn Skill Assessment: CSS", "issuer": "LinkedIn", "date": "Passed"},
    ],
    "projects": [
        {
            "name": "AI-Powered Multi-Agent Research System",
            "description": "Advanced multi-agent AI system for automated research tasks. Integrates multiple AI agents working collaboratively with Docker containerization and PostgreSQL for data persistence.",
            "technologies": ["Python", "Docker", "PostgreSQL", "Multi-Agent AI", "LangChain"],
            "url": "GitHub (Private)"
        },
        {
            "name": "Plataforma de Asistente con IA",
            "description": "Aplicación Python que integra capacidades de IA agéntica con consumo de APIs REST y flujos de trabajo de automatización. Desarrollo de endpoints REST personalizados e integración con APIs de OpenAI y Anthropic Claude",
            "technologies": ["Python", "FastAPI", "OpenAI API", "Anthropic Claude API", "APIs REST"],
            "url": "Not provided"
        },
        {
            "name": "littleShop",
            "description": "Sitio web que permite a usuarios gestionar pequeñas tiendas con recursos limitados",
            "technologies": ["Vite", "React", "TypeScript"],
            "url": "Live-Preview"
        },
        {
            "name": "Sell It",
            "description": "Plataforma de e-commerce que permite a usuarios vender o comprar productos online. Incluye gestión de productos, navegación por categorías y panel de administración",
            "technologies": ["Ruby on Rails", "PostgreSQL", "Redis"],
            "url": "Live-Preview"
        },
        {
            "name": "Ticket Admin",
            "description": "Sistema de gestión de tickets para empresas, construido con stack MERN. Incluye autenticación, gestión de roles y API REST completa",
            "technologies": ["MongoDB", "Express", "React", "Node.js"],
            "url": "Live-Preview"
        }
    ],
    "publications": [],
    "awards": [],
    "volunteer": [
        {
            "role": "Mentor (Voluntario)",
            "organization": "Microverse",
            "duration": "Noviembre 2022 – Presente",
            "description": "Mentoría a desarrolladores web junior, proporcionando soporte técnico mediante revisiones de código"
        }
    ],
    "notable_achievements": [
        "1300+ horas de formación en desarrollo full-stack",
        "Experiencia mentoreando equipos de 5+ desarrolladores",
        "Mejora del 15% en calidad y eficiencia de proyectos como mentor",
        "Aumento del 50% en tareas completadas bajo su mentoría",
        "100% de feedback positivo del equipo",
        "Aumento del 25% en productividad implementando Six Sigma",
        "Reducción del 15% en desperdicios en producción",
        "Gestión de 20+ empleados",
        "Mejora del 30% en cumplimiento de seguridad",
        "Reducción del 20% en errores de inventario"
    ]
}


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file for metadata purposes."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Warning: Could not extract raw text from PDF: {e}", file=sys.stderr)
        return None


def get_user_data():
    """
    Returns a deep copy of the hardcoded user data.
    Use this function to get user data without risk of modifying the original.
    """
    return copy.deepcopy(HARDCODED_USER_DATA)


def print_update_instructions(field_path: str, new_data: dict) -> None:
    """
    Utility to help user add new information to HARDCODED_USER_DATA.
    Prints the code snippet that should be added to this file.

    Args:
        field_path: Dot-separated path to the field (e.g., "work_experience", "technical_skills.programming_languages")
        new_data: The data to add
    """
    print("\n" + "="*60)
    print("TO UPDATE YOUR CV DATA:")
    print("="*60)
    print(f"\nAdd the following to HARDCODED_USER_DATA['{field_path}']:")
    print(f"\n{json.dumps(new_data, indent=2, ensure_ascii=False)}")
    print("\nEdit this file: execution/analyze_master_cv.py")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Load CV data from hardcoded user information')
    parser.add_argument('--cv', default='resources/job_applications/master_cv.pdf',
                       help='Path to master CV PDF (used for raw text metadata only)')
    parser.add_argument('--output', default='.tmp/job_applications/cv_database.json',
                       help='Output JSON file path')

    args = parser.parse_args()

    cv_path = Path(args.cv)
    output_path = Path(args.output)

    print("Loading CV data from hardcoded user information...")

    # Get a copy of hardcoded data
    cv_database = get_user_data()

    # Extract raw text from PDF if available (for metadata only)
    raw_text = None
    if cv_path.exists():
        print(f"Extracting raw text from: {cv_path}")
        raw_text = extract_text_from_pdf(cv_path)
        if raw_text:
            print(f"  Extracted {len(raw_text)} characters for metadata")
    else:
        print(f"Note: CV file not found at {cv_path} (raw text metadata will be empty)")

    # Add metadata
    cv_database['metadata'] = {
        'source_file': str(cv_path),
        'raw_text': raw_text or "",
        'data_source': 'hardcoded'
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save database
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cv_database, f, indent=2, ensure_ascii=False)

    print(f"\n✓ CV database saved to: {output_path}")
    print(f"\nUser information:")
    print(f"  Name: {cv_database['personal_info']['name']}")
    print(f"  Work experiences: {len(cv_database['work_experience'])}")
    print(f"  Education entries: {len(cv_database['education'])}")
    print(f"\n💡 To update your CV data, edit HARDCODED_USER_DATA in this file:")
    print(f"   execution/analyze_master_cv.py")

    return 0


if __name__ == '__main__':
    sys.exit(main())
