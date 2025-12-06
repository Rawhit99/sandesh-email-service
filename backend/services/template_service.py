import re
import html
from bs4 import BeautifulSoup
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape, TemplateSyntaxError
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Set, Union
from datetime import datetime
from fastapi import HTTPException
import time
import uuid

from models.models import EmailTemplate
from models.schemas import TemplateCreate, TemplateResponse, TemplateUpdate

class TemplateService:
    def __init__(self):
        # Initialize Jinja2 environment for template rendering
        self.jinja_env = Environment(
            loader=FileSystemLoader('app/templates/email'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        # Keep only system-critical reserved variables
        self.reserved_variables = {'email', 'date'}  # Removed 'name' from reserved variables
    
    def get_templates(self, db: Session, limit: int = 100, offset: int = 0, active_only: bool = False) -> List[TemplateResponse]:
        """Get email templates with optional filtering by active status"""
        try:
            query = db.query(EmailTemplate)
            
            # Only filter by active status if requested
            if active_only:
                query = query.filter(EmailTemplate.is_active.is_(True))
            
            templates = query.order_by(EmailTemplate.created_at.desc()).offset(offset).limit(limit).all()
            
            return [TemplateResponse.from_orm(template) for template in templates]
        except Exception as e:
            raise ValueError(f"Failed to fetch templates: {str(e)}")
    
    def get_template_by_id(self, db: Session, template_id: str) -> Optional[TemplateResponse]:
        """Get specific template by template_id"""
        try:
            template = db.query(EmailTemplate).filter(
                EmailTemplate.template_id == template_id
            ).first()
            
            return TemplateResponse.from_orm(template) if template else None
        except Exception as e:
            raise ValueError(f"Failed to fetch template: {str(e)}")
    
    def create_template(self, db: Session, template: TemplateCreate) -> TemplateResponse:
        """Create a new email template"""
        # Check if template_id already exists
        existing_template = db.query(EmailTemplate).filter(
            EmailTemplate.template_id == template.template_id
        ).first()
        
        if existing_template:
            raise HTTPException(status_code=400, detail=f"Template ID '{template.template_id}' already exists")
        
        sanitized_content = template.content
        variables_dict = {var: "" for var in template.variables}

        print("DEBUG is_active value and type:", template.is_active, type(template.is_active))

        # Force is_active to boolean, no matter what
        is_active = template.is_active
        if isinstance(is_active, str):
            is_active = is_active.lower() == "true"
        elif not isinstance(is_active, bool):
            is_active = bool(is_active)
        print("DEBUG: is_active value and type before insert:", is_active, type(is_active))

        data = template.dict()
        data["is_active"] = is_active
        db_template = EmailTemplate(**data)

        try:
            db.add(db_template)
            db.commit()
            db.refresh(db_template)
            return TemplateResponse.from_orm(db_template)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")
    
    def update_template(self, db: Session, template_id: str, template: TemplateUpdate) -> TemplateResponse:
        db_template = db.query(EmailTemplate).filter(EmailTemplate.template_id == template_id).first()
        if not db_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Track if we need to re-extract variables
        should_extract_variables = False
        
        # Only update fields that are provided
        if template.name is not None:
            db_template.name = template.name
        if template.subject is not None:
            db_template.subject = template.subject
            should_extract_variables = True
        if template.content is not None:
            db_template.content = template.content
            should_extract_variables = True
        
        # Auto-extract variables if content or subject changed
        # Ignore variables from frontend to ensure they match the actual template
        if should_extract_variables:
            from models.schemas import TemplateCreate
            extracted_vars = TemplateCreate.extract_variables(db_template.content, db_template.subject)
            db_template.variables = extracted_vars
        
        if template.is_active is not None:
            is_active = template.is_active
            if isinstance(is_active, str):
                is_active = is_active.lower() == "true"
            db_template.is_active = is_active
        
        try:
            db.commit()
            db.refresh(db_template)
            return TemplateResponse.from_orm(db_template)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error updating template: {str(e)}")
    
    def delete_template(self, db: Session, template_id: str) -> bool:
        """Hard delete a template from the database"""
        try:
            db_template = db.query(EmailTemplate).filter(
                EmailTemplate.template_id == template_id
            ).first()
            
            if not db_template:
                return False
            
            # Perform hard delete
            db.delete(db_template)
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to delete template: {str(e)}")
    
    def render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """Render template with provided context using Jinja2"""
        try:
            template = Template(template_content)
            return template.render(**context)
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error: {str(e)}")
        except Exception as e:
            # Fallback to simple string replacement for basic templates
            try:
                rendered = template_content
                for key, value in context.items():
                    placeholder = f"{{{{{key}}}}}"
                    rendered = rendered.replace(placeholder, str(value))
                return rendered
            except Exception as e2:
                raise ValueError(f"Failed to render template: {str(e2)}")
    
    def validate_template_syntax(self, template_content: str, variables: Union[Dict[str, str], List[str]] = None) -> Dict[str, Any]:
        """Validate template syntax and extract variables"""
        try:
            # First, unescape HTML entities
            unescaped_content = html.unescape(template_content)
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(unescaped_content, 'html.parser')
            
            # Remove all style attributes
            for tag in soup.find_all(attrs={"style": True}):
                del tag["style"]
            
            # Remove all color spans
            for span in soup.find_all("span", style=lambda x: x and "color:" in x):
                span.unwrap()
            
            # Get the cleaned HTML
            cleaned_content = str(soup)
            
            # Extract variables using regex
            found_variables = set()
            
            # Find all Jinja2 variables in the content
            jinja_vars = re.findall(r'\{\{\s*(\w+)\s*\}\}', cleaned_content)
            found_variables.update(jinja_vars)
            
            # Also look for variables in HTML attributes
            for tag in soup.find_all():
                for attr in tag.attrs:
                    if isinstance(tag[attr], str):
                        attr_vars = re.findall(r'\{\{\s*(\w+)\s*\}\}', tag[attr])
                        found_variables.update(attr_vars)
            
            # Convert variables to list if it's a dict
            if isinstance(variables, dict):
                variables = list(variables.keys())
            
            # Check if all found variables are in the provided variables list
            if variables and not all(var in variables for var in found_variables):
                missing_vars = found_variables - set(variables)
                return {
                    "valid": False,
                    "variables": list(found_variables),
                    "error": f"Missing variables in template: {', '.join(missing_vars)}"
                }
            
            # Only check for invalid variables (those that might conflict with system variables)
            invalid_vars = found_variables.intersection(self.reserved_variables)
            if invalid_vars:
                return {
                    "valid": False,
                    "variables": list(found_variables),
                    "error": f"Reserved variables cannot be used: {', '.join(invalid_vars)}"
                }
            
            return {
                "valid": True,
                "variables": list(found_variables),
                "error": None
            }
        except Exception as e:
            return {
                "valid": False,
                "variables": [],
                "error": f"Template validation error: {str(e)}"
            }
    
    def preview_template(self, template_content: str, sample_data: Dict[str, Any]) -> str:
        """Preview template with sample data"""
        try:
            return self.render_template(template_content, sample_data)
        except Exception as e:
            raise ValueError(f"Failed to preview template: {str(e)}")

    def validate_template_content(self, content: str) -> bool:
        """Validate that the template contains all required variables"""
        for var in self.required_variables:
            if f"{{{{{var}}}}}" not in content:
                return False
        return True