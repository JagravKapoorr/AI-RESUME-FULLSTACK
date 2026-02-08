import PyPDF2
import docx
import os
from typing import Dict, Optional
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from django.conf import settings

# Import schemas
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from schemas import ResumeParsedSchema, SimpleResumeParsedSchema


class ResumeParser:
    """Parse resumes using LangChain and OpenAI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the parser with GROQ_API_KEY"""
        self.api_key = api_key or getattr(settings, 'GROQ_API_KEY', None)
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set GROQ_API_KEY in settings or .env")
        
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",  # Cost-effective model
            temperature=0,  # Deterministic for parsing
            api_key=self.api_key
        )
        
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
        return text.strip()
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")
        return text.strip()
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text based on file type"""
        if file_type.lower() == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_type.lower() in ['docx', 'doc']:
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def parse_resume(self, file_path: str, file_type: str, use_simple: bool = False) -> Dict:
        """
        Parse resume and extract structured data
        
        Args:
            file_path: Path to resume file
            file_type: File extension (pdf, docx, doc)
            use_simple: Use simplified schema (cheaper, faster)
        
        Returns:
            Dictionary with parsed resume data
        """
        
        # Extract text from file
        resume_text = self.extract_text(file_path, file_type)
        
        if not resume_text.strip():
            raise ValueError("No text could be extracted from the resume")
        
        # Choose schema
        schema = SimpleResumeParsedSchema if use_simple else ResumeParsedSchema
        parser = PydanticOutputParser(pydantic_object=schema)
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert resume parser.

            Extract information EXACTLY according to the provided schema.

            Rules:
            - Output ONLY valid JSON that conforms to the schema
            - Do NOT include explanations, markdown, or additional text
            - Do NOT infer or calculate values
            - If information is missing, use null or empty arrays
            - Preserve original wording and date formats exactly as written
            - Extract skills from both the skills section and experience descriptions

            {format_instructions}
            """),
                ("user", "Parse the following resume text:\n\n{resume_text}")
            ])

        
        # Format the prompt
        formatted_prompt = prompt.format_messages(
            format_instructions=parser.get_format_instructions(),
            resume_text=resume_text
        )
        
        # Get response from LLM
        response = self.llm.invoke(formatted_prompt)
        
        # Parse the response
        try:
            parsed_data = parser.parse(response.content)
            return parsed_data.dict()
        except Exception as e:
            raise Exception(f"Error parsing LLM response: {str(e)}\n\nResponse: {response.content[:500]}")