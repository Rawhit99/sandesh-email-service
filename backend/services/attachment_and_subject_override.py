novu_context = {
            "organisation": org.name,
            "org_logo": org.logo,
            "vendor_name": vendor.name,
            "due_date": str(assessment.due_date.strftime("%B %d, %Y"))
            if assessment.due_date
            else None,
            "assessment_name": assessment.name,
        }
        if not is_on_premise and Config.FE_ASSESSMENT_HOST:
            assessment_url = f"{Config.FE_ASSESSMENT_HOST}?assessment_id={assessment.id}&organization_id={org.org_id}"
            assessment_url += f"&member_id={spoc_member.id}" if spoc_member else ""
            novu_context["url"] = assessment_url
        else:
            # For on-premise deployments, attach the assessment template
            try:
                # Generate assessment template Excel file
                template_buffer = await self.export_questions(
                    assessment_id=assessment.id,
                    filter_completion=None,  # Export all questions
                )
                template_buffer.seek(0)
                template_content = template_buffer.read()
                # Encode to base64 for email attachment
                template_base64 = base64.b64encode(template_content).decode("utf-8")

                # Generate filename - use config filename if set (for enterprise whitelisting)
                # Otherwise use assessment name
                filename = (
                    Config.ASSESSMENT_TEMPLATE_FILENAME or f"{assessment.name}.xlsx"
                )

                # Add attachment to payload directly
                novu_context["attachments"] = [
                    {
                        "file": template_base64,
                        "name": filename,
                        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    }
                ]
            except Exception as e:
                dprint(
                    f"Failed to attach assessment template for assessment {assessment.id}: {e}",
                    level="warning",
                )

        override: dict = {"email": {"cc": cc_emails}}

        if is_reminder:
            override["email"]["subject"] = (
                f"Reminder! {assessment.name} {org.name} - {vendor.name}"
            )

        # INFO: contact id should be created for vendor's SPOC already
        if not vendor.contact_id:
            raise RequestDataException(
                message="Please add vendor's SPOC email to send the assessment to"
            )
        self.notification.vendor_assessment_form_to_vendor(
            str(vendor.contact_id), novu_context, override
        )
        return cc_emails