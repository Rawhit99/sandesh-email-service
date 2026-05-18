import html
import re
from typing import Any, Dict, List, Optional, Union

from bs4 import BeautifulSoup
from exceptions import BadRequestError, NotFoundError
from jinja2 import (
    Environment,
    FileSystemLoader,
    TemplateSyntaxError,
    select_autoescape,
)
from jinja2.sandbox import SandboxedEnvironment
from models.models import EmailTemplate, Organization, OrgTemplateSetting
from models.schema_domains.templates import (
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
)
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def resolve_email_template_row(
    db: Session, template_id: str, user_id: Optional[int]
) -> Optional[EmailTemplate]:
    """Pick tenant-owned row first, then legacy shared row."""
    if user_id is not None:
        row = (
            db.query(EmailTemplate)
            .filter(
                EmailTemplate.template_id == template_id,
                EmailTemplate.user_id == user_id,
            )
            .first()
        )
        if row:
            return row
    return (
        db.query(EmailTemplate)
        .filter(
            EmailTemplate.template_id == template_id,
            EmailTemplate.user_id.is_(None),
        )
        .first()
    )


def _resolve_scope_organization(
    db: Session,
    scope_user_id: Optional[int],
) -> Optional[Organization]:
    if scope_user_id is None:
        return None
    return (
        db.query(Organization)
        .filter(Organization.service_user_id == scope_user_id)
        .first()
    )


def _effective_enabled_map(
    db: Session,
    organization_id: int,
    template_ids: List[str],
) -> Dict[str, bool]:
    if not template_ids:
        return {}
    rows = (
        db.query(OrgTemplateSetting)
        .filter(
            OrgTemplateSetting.organization_id == organization_id,
            OrgTemplateSetting.template_id.in_(template_ids),
        )
        .all()
    )
    return {row.template_id: bool(row.is_enabled) for row in rows}


def seed_templates_for_owner(db: Session, owner_user_id: int) -> None:
    """Copy existing logical templates into a new tenant owner scope."""
    existing_rows = (
        db.query(EmailTemplate.template_id)
        .filter(EmailTemplate.user_id == owner_user_id)
        .all()
    )
    existing_template_ids = {row[0] for row in existing_rows}

    source_rows = (
        db.query(EmailTemplate)
        .filter(
            or_(
                EmailTemplate.user_id.is_(None),
                EmailTemplate.user_id != owner_user_id,
            )
        )
        .order_by(
            EmailTemplate.template_id.asc(),
            EmailTemplate.updated_at.desc(),
            EmailTemplate.created_at.desc(),
        )
        .all()
    )

    seen_template_ids = set()
    for source in source_rows:
        if (
            source.template_id in seen_template_ids
            or source.template_id in existing_template_ids
        ):
            continue
        seen_template_ids.add(source.template_id)
        db.add(
            EmailTemplate(
                template_id=source.template_id,
                user_id=owner_user_id,
                name=source.name,
                subject=source.subject,
                content=source.content,
                variables=source.variables or {},
                default_attachments=source.default_attachments,
                is_active=source.is_active,
            )
        )


class TemplateService:
    def __init__(self):
        # Initialize Jinja2 environment for template rendering
        self.jinja_env = Environment(
            loader=FileSystemLoader("app/templates/email"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        # Keep only system-critical reserved variables
        self.reserved_variables = {
            "email",
            "date",
        }  # Removed 'name' from reserved variables

    def get_templates(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        active_only: bool = False,
        scope_user_id: Optional[int] = None,
    ) -> List[TemplateResponse]:
        """List templates for one tenant."""
        query = db.query(EmailTemplate)
        if scope_user_id is not None:
            query = query.filter(EmailTemplate.user_id == scope_user_id)

        templates = (
            query.order_by(EmailTemplate.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        org = _resolve_scope_organization(db, scope_user_id)
        enabled_map: Dict[str, bool] = {}
        if org:
            enabled_map = _effective_enabled_map(
                db,
                org.id,
                [t.template_id for t in templates],
            )

        out: List[TemplateResponse] = []
        for template in templates:
            row = TemplateResponse.from_orm(template)
            org_enabled = enabled_map.get(template.template_id, True)
            row.is_active = bool(template.is_active) and bool(org_enabled)
            if active_only and not row.is_active:
                continue
            out.append(row)
        return out

    def get_template_by_id(
        self,
        db: Session,
        template_id: str,
        scope_user_id: Optional[int] = None,
    ) -> Optional[TemplateResponse]:
        """Get template by slug for one tenant when scope_user_id is set."""
        q = db.query(EmailTemplate).filter(
            EmailTemplate.template_id == template_id
        )
        if scope_user_id is not None:
            q = q.filter(EmailTemplate.user_id == scope_user_id)
        template = q.first()
        if not template:
            return None
        row = TemplateResponse.from_orm(template)
        org = _resolve_scope_organization(db, scope_user_id)
        if org:
            enabled_map = _effective_enabled_map(
                db, org.id, [template.template_id]
            )
            org_enabled = enabled_map.get(template.template_id, True)
            row.is_active = bool(template.is_active) and bool(org_enabled)
        return row

    def create_template(
        self, db: Session, template: TemplateCreate, owner_user_id: int
    ) -> TemplateResponse:
        """Create a template owned by owner_user_id."""
        existing_template = (
            db.query(EmailTemplate)
            .filter(
                EmailTemplate.template_id == template.template_id,
                EmailTemplate.user_id == owner_user_id,
            )
            .first()
        )

        if existing_template:
            raise BadRequestError(
                f"Template ID '{template.template_id}' already exists "
                "for this account"
            )

        is_active = template.is_active
        if isinstance(is_active, str):
            is_active = is_active.lower() == "true"
        elif not isinstance(is_active, bool):
            is_active = bool(is_active)

        data = template.model_dump()
        data["is_active"] = is_active
        data["user_id"] = owner_user_id
        db_template = EmailTemplate(**data)

        try:
            db.add(db_template)
            # Persist source row before fan-out so unique checks are accurate.
            db.flush()
            self._replicate_template_to_all_orgs(
                db=db,
                template_data=data,
                source_owner_user_id=owner_user_id,
            )
            db.commit()
            db.refresh(db_template)
            return TemplateResponse.from_orm(db_template)
        except SQLAlchemyError as e:
            db.rollback()
            raise ValueError(f"Error creating template: {str(e)}")

    def _replicate_template_to_all_orgs(
        self,
        db: Session,
        template_data: Dict[str, Any],
        source_owner_user_id: int,
    ) -> None:
        """Replicate new template to every org tenant account.

        Keep existing rows untouched so per-org enable/disable state remains
        intact.
        """
        all_org_service_users = (
            db.query(Organization.service_user_id)
            .filter(Organization.service_user_id.isnot(None))
            .all()
        )
        if not all_org_service_users:
            return

        template_id = str(template_data.get("template_id", "")).strip()
        if not template_id:
            return

        service_user_ids = [
            row[0]
            for row in all_org_service_users
            if row[0] is not None and row[0] != source_owner_user_id
        ]
        if not service_user_ids:
            return

        existing_rows = (
            db.query(EmailTemplate.user_id)
            .filter(
                EmailTemplate.template_id == template_id,
                EmailTemplate.user_id.in_(service_user_ids),
            )
            .all()
        )
        existing_user_ids = {
            row[0] for row in existing_rows if row[0] is not None
        }

        for target_user_id in service_user_ids:
            if target_user_id in existing_user_ids:
                continue
            cloned = dict(template_data)
            cloned["user_id"] = target_user_id
            db.add(EmailTemplate(**cloned))

    def update_template(
        self,
        db: Session,
        template_id: str,
        template: TemplateUpdate,
        scope_user_id: int,
    ) -> TemplateResponse:
        db_template = (
            db.query(EmailTemplate)
            .filter(
                EmailTemplate.template_id == template_id,
                EmailTemplate.user_id == scope_user_id,
            )
            .first()
        )
        if not db_template:
            raise NotFoundError("Template not found")

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
        # Ignore frontend variables to ensure they match actual template.
        if should_extract_variables:
            from models.schema_domains.templates import TemplateCreate

            extracted_vars = TemplateCreate.extract_variables(
                db_template.content, db_template.subject
            )
            db_template.variables = extracted_vars

        if template.is_active is not None:
            is_active = template.is_active
            if isinstance(is_active, str):
                is_active = is_active.lower() == "true"
            db_template.is_active = is_active

        if template.default_attachments is not None:
            db_template.default_attachments = template.default_attachments

        try:
            db.commit()
            db.refresh(db_template)
            return TemplateResponse.from_orm(db_template)
        except SQLAlchemyError as e:
            db.rollback()
            raise ValueError(f"Error updating template: {str(e)}")

    def delete_template(
        self, db: Session, template_id: str, scope_user_id: int
    ) -> bool:
        """Hard delete a tenant-owned template."""
        try:
            db_template = (
                db.query(EmailTemplate)
                .filter(
                    EmailTemplate.template_id == template_id,
                    EmailTemplate.user_id == scope_user_id,
                )
                .first()
            )

            if not db_template:
                return False

            # Perform hard delete
            db.delete(db_template)
            db.commit()

            return True
        except SQLAlchemyError as e:
            db.rollback()
            raise ValueError(f"Failed to delete template: {str(e)}")

    def render_template(
        self, template_content: str, context: Dict[str, Any]
    ) -> str:
        """Render template with provided context using sandboxed Jinja2"""
        try:
            env = SandboxedEnvironment(
                autoescape=select_autoescape(["html", "xml"])
            )
            template = env.from_string(template_content)
            return template.render(**context)
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error: {str(e)}")
        except (TypeError, ValueError, KeyError, AttributeError):
            # Fallback to simple string replacement for basic templates
            try:
                rendered = template_content
                for key, value in context.items():
                    placeholder = f"{{{{{key}}}}}"
                    rendered = rendered.replace(placeholder, str(value))
                return rendered
            except (TypeError, ValueError, KeyError, AttributeError) as e2:
                raise ValueError(f"Failed to render template: {str(e2)}")

    def validate_template_syntax(
        self,
        template_content: str,
        variables: Union[Dict[str, str], List[str]] = None,
    ) -> Dict[str, Any]:
        """Validate template syntax and extract variables"""
        try:
            # First, unescape HTML entities
            unescaped_content = html.unescape(template_content)

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(unescaped_content, "html.parser")

            # Remove all style attributes
            for tag in soup.find_all(attrs={"style": True}):
                del tag["style"]

            # Remove all color spans
            for span in soup.find_all(
                "span", style=lambda x: x and "color:" in x
            ):
                span.unwrap()

            # Get the cleaned HTML
            cleaned_content = str(soup)

            # Extract variables using regex
            found_variables = set()

            # Find all Jinja2 variables in the content
            jinja_vars = re.findall(r"\{\{\s*(\w+)\s*\}\}", cleaned_content)
            found_variables.update(jinja_vars)

            # Also look for variables in HTML attributes
            for tag in soup.find_all():
                for attr in tag.attrs:
                    if isinstance(tag[attr], str):
                        attr_vars = re.findall(
                            r"\{\{\s*(\w+)\s*\}\}", tag[attr]
                        )
                        found_variables.update(attr_vars)

            # Convert variables to list if it's a dict
            if isinstance(variables, dict):
                variables = list(variables.keys())

            # Check if all found variables are in the provided variables list
            if variables and not all(
                var in variables for var in found_variables
            ):
                missing_vars = found_variables - set(variables)
                return {
                    "valid": False,
                    "variables": list(found_variables),
                    "error": (
                        "Missing variables in template: "
                        f"{', '.join(missing_vars)}"
                    ),
                }

            # Check only reserved variables that conflict with system usage.
            invalid_vars = found_variables.intersection(
                self.reserved_variables
            )
            if invalid_vars:
                return {
                    "valid": False,
                    "variables": list(found_variables),
                    "error": (
                        "Reserved variables cannot be used: "
                        f"{', '.join(invalid_vars)}"
                    ),
                }

            return {
                "valid": True,
                "variables": list(found_variables),
                "error": None,
            }
        except (TypeError, ValueError, AttributeError, re.error) as e:
            return {
                "valid": False,
                "variables": [],
                "error": f"Template validation error: {str(e)}",
            }

    def preview_template(
        self, template_content: str, sample_data: Dict[str, Any]
    ) -> str:
        """Preview template with sample data"""
        return self.render_template(template_content, sample_data)

    def validate_template_content(self, content: str) -> bool:
        """Validate that the template contains all required variables"""
        for var in self.required_variables:
            if f"{{{{{var}}}}}" not in content:
                return False
        return True
