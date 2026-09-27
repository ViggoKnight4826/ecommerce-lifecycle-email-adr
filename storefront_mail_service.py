from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from infrai_client import InfraiError, infrai
from template_catalog import (
    LifecycleKind,
    TemplatePreviewRequest,
    TemplateRegistrationRequest,
    build_template_definition,
    order_template_vars,
)

app = FastAPI(title="Storefront lifecycle email templates")


class RegisteredTemplate(BaseModel):
    kind: LifecycleKind
    name: str
    template_id: str


class RegistrationResponse(BaseModel):
    templates: list[RegisteredTemplate]


class PreviewResponse(BaseModel):
    kind: LifecycleKind
    template_id: str
    preview: dict


@app.post("/templates/register", response_model=RegistrationResponse)
def register_templates(request: TemplateRegistrationRequest) -> RegistrationResponse:
    results: list[RegisteredTemplate] = []
    for kind in LifecycleKind:
        definition = build_template_definition(kind, request.store_name, request.namespace)
        try:
            reply = infrai.email.template.create(
                {
                    "name": definition.name,
                    "subject": definition.subject,
                    "html": definition.html,
                },
                idempotency_key=f"{request.namespace}:{kind.value}",
            )
        except InfraiError as exc:
            raise HTTPException(status_code=400, detail={"code": exc.code, "error": exc.error}) from exc
        data = reply["data"]
        results.append(
            RegisteredTemplate(
                kind=kind,
                name=definition.name,
                template_id=str(data["id"]),
            )
        )
    return RegistrationResponse(templates=results)


@app.post("/templates/preview", response_model=PreviewResponse)
def preview_template(request: TemplatePreviewRequest) -> PreviewResponse:
    try:
        reply = infrai.email.template.preview(
            request.template_id,
            {"vars": order_template_vars(request.order)},
        )
    except InfraiError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "error": exc.error}) from exc
    return PreviewResponse(kind=request.kind, template_id=request.template_id, preview=reply["data"])
