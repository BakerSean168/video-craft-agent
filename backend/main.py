import json

from fastapi import FastAPI, HTTPException

from core.config import get_settings
from core.models import VideoRequirement
from services.dify_client import DifyClient, DifyError
from api.video_jobs import router as video_jobs_router
from api.assets import router as assets_router


app = FastAPI(title="VideoCraft Agent API")
app.include_router(video_jobs_router)
app.include_router(assets_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title=app.title,
        version="0.1.0",
        description="VideoCraft Agent API documentation",
        routes=app.routes,
    )
    # Customize schema to force Swagger UI to show file picker for files[]
    try:
        schemas = openapi_schema.get("components", {}).get("schemas", {})
        for schema_name, schema in schemas.items():
            if "properties" in schema:
                for prop_name, prop in schema["properties"].items():
                    if prop_name == "files[]" and "items" in prop:
                        prop["items"] = {
                            "type": "string",
                            "format": "binary"
                        }
    except Exception as e:
        import sys
        print(f"Error customizing OpenAPI schema: {e}", file=sys.stderr)
        
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
def read_root():
    """Redirect root path to interactive OpenAPI docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/dify/run")
def run_dify_workflow(requirement: VideoRequirement) -> dict:
    settings = get_settings()

    try:
        client = DifyClient.from_settings(settings)
        result = client.run_workflow(requirement.to_dify_inputs())
    except DifyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return result.model_dump()


def main() -> None:
    settings = get_settings()
    client = DifyClient.from_settings(settings)
    sample = VideoRequirement(
        product_name="AI 编程课",
        target_audience="想转行 AI 的程序员",
        selling_points=["零基础入门 AI Agent", "带项目实战", "适合 Python 初学者"],
        style="科技感、快节奏",
        platform="douyin",
        duration_seconds=15,
    )
    result = client.run_workflow(sample.to_dify_inputs())
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
