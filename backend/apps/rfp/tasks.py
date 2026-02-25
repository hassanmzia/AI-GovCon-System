import asyncio
import logging
import os

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_rfp_upload(self, document_id: str):
    """
    Extract text from an uploaded RFP document (PDF/DOCX), run the
    parser to identify requirements, and create RFPRequirement and
    ComplianceMatrixItem records.

    Steps:
      1. Load the RFPDocument record and update status to 'processing'.
      2. Read the file and extract raw text (PDF via PyPDF2, DOCX via
         python-docx, plain text via direct read).
      3. Run RFPParser.extract_requirements() on the extracted text.
      4. Create RFPRequirement rows for each extracted requirement.
      5. Create a ComplianceMatrixItem for each requirement.
      6. Update the document with extracted metadata and set status
         to 'completed'.
    """
    from apps.rfp.models import ComplianceMatrixItem, RFPDocument, RFPRequirement
    from apps.rfp.services.parser import RFPParser

    try:
        document = RFPDocument.objects.get(pk=document_id)
    except RFPDocument.DoesNotExist:
        logger.error("RFPDocument %s not found. Aborting extraction.", document_id)
        return

    document.extraction_status = "processing"
    document.save(update_fields=["extraction_status", "updated_at"])

    try:
        # -- Step 2: Extract raw text based on file type ---------------
        extracted_text = ""
        file_type = (document.file_type or "").lower()
        file_path = document.file.name  # storage-relative path

        if file_type == "pdf":
            extracted_text = _extract_text_from_pdf(document.file)
        elif file_type in ("docx", "doc"):
            extracted_text = _extract_text_from_docx(document.file)
        elif file_type in ("txt", "text"):
            document.file.open("r")
            extracted_text = document.file.read()
            document.file.close()
        else:
            logger.warning(
                "Unsupported file type '%s' for document %s. "
                "Storing empty extracted text.",
                file_type,
                document_id,
            )

        document.extracted_text = extracted_text

        # -- Step 3: Parse requirements --------------------------------
        parser = RFPParser()
        requirements_data = asyncio.run(
            parser.extract_requirements(extracted_text)
        )

        # -- Step 4: Create RFPRequirement rows ------------------------
        created_requirements = []
        for req in requirements_data:
            rfp_req = RFPRequirement.objects.create(
                rfp_document=document,
                requirement_id=req["requirement_id"],
                requirement_text=req["requirement_text"],
                requirement_type=req.get("requirement_type", "mandatory"),
                category=req.get("category", ""),
                section_reference=req.get("section_reference", ""),
            )
            created_requirements.append(rfp_req)

        # -- Step 5: Create ComplianceMatrixItem for each requirement --
        for rfp_req in created_requirements:
            ComplianceMatrixItem.objects.create(
                rfp_document=document,
                requirement=rfp_req,
                compliance_status="not_assessed",
                response_status="not_started",
            )

        # -- Step 6: Update document metadata --------------------------
        document.extraction_status = "completed"
        document.save(
            update_fields=[
                "extracted_text",
                "extraction_status",
                "updated_at",
            ]
        )

        logger.info(
            "Successfully processed document %s: extracted %d requirements.",
            document_id,
            len(created_requirements),
        )

    except Exception as exc:
        document.extraction_status = "failed"
        document.save(update_fields=["extraction_status", "updated_at"])
        logger.exception(
            "Failed to process document %s: %s", document_id, exc
        )
        raise self.retry(exc=exc)


@shared_task(bind=True)
def check_for_amendments(self):
    """
    Periodically check SAM.gov for amendments on active RFP documents.

    For each RFPDocument linked to an active deal, query SAM.gov (or a
    cached feed) for new amendments. When found, create Amendment records
    and flag material changes that require compliance matrix updates.
    """
    from apps.rfp.models import Amendment, RFPDocument
    from apps.rfp.services.diff_tracker import AmendmentDiffTracker

    tracker = AmendmentDiffTracker()

    # Get active documents (those linked to deals that are not archived/closed)
    active_documents = RFPDocument.objects.filter(
        extraction_status="completed",
    ).select_related("deal")

    logger.info(
        "Checking amendments for %d active RFP documents.",
        active_documents.count(),
    )

    for document in active_documents:
        try:
            # Resolve the SAM.gov notice_id via deal -> opportunity
            opportunity = getattr(document.deal, "opportunity", None)
            if not opportunity or not opportunity.notice_id:
                logger.debug(
                    "Document %s has no linked SAM.gov opportunity. Skipping.",
                    document.id,
                )
                continue

            notice_id = opportunity.notice_id

            # Call SAM.gov to get related notices (amendments)
            from apps.opportunities.services.samgov_client import SAMGovClient

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            client = SAMGovClient()
            try:
                sam_amendments = loop.run_until_complete(
                    client.check_amendments(notice_id)
                )
            finally:
                loop.run_until_complete(client.close())
                loop.close()

            for i, sam_amend in enumerate(sam_amendments, 1):
                if not Amendment.objects.filter(
                    rfp_document=document,
                    amendment_number=i,
                ).exists():
                    changes = tracker.compute_diff(
                        document.extracted_text or "",
                        sam_amend.get("description", "") or sam_amend.get("body", ""),
                    )
                    is_material = tracker.assess_materiality(changes)
                    Amendment.objects.create(
                        rfp_document=document,
                        amendment_number=i,
                        title=sam_amend.get("title", ""),
                        summary=sam_amend.get("description", ""),
                        changes=changes,
                        is_material=is_material,
                        requires_compliance_update=is_material,
                    )

            logger.debug(
                "Amendment check for document %s (deal %s): %d related notices found.",
                document.id,
                document.deal_id,
                len(sam_amendments),
            )
        except Exception:
            logger.exception(
                "Error checking amendments for document %s.", document.id
            )

    logger.info("Amendment check complete.")


# ── Helper functions for text extraction ─────────────────────


def _extract_text_from_pdf(file_field) -> str:
    """Extract text from a PDF file using PyPDF2."""
    try:
        from PyPDF2 import PdfReader

        file_field.open("rb")
        reader = PdfReader(file_field)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        file_field.close()
        return "\n\n".join(pages)
    except ImportError:
        logger.warning(
            "PyPDF2 is not installed. Cannot extract text from PDF."
        )
        return ""
    except Exception:
        logger.exception("Failed to extract text from PDF.")
        return ""


def _extract_text_from_docx(file_field) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        from docx import Document

        file_field.open("rb")
        doc = Document(file_field)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        file_field.close()
        return "\n\n".join(paragraphs)
    except ImportError:
        logger.warning(
            "python-docx is not installed. Cannot extract text from DOCX."
        )
        return ""
    except Exception:
        logger.exception("Failed to extract text from DOCX.")
        return ""
