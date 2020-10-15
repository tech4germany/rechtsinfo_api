import fastapi
import starlette


class ApiException(Exception):
    def __init__(self, status_code, title, detail):
        self.status_code = status_code
        self.title = title
        self.detail = detail


def build_error_response(status_code, title, detail=None):
    error = {"code": status_code, "title": title}
    if detail:
        error["detail"] = detail

    return fastapi.responses.JSONResponse(status_code=status_code, content={"errors": [error]})


async def api_exception_handler(request: fastapi.Request, exc: ApiException):
    return build_error_response(exc.status_code, exc.title, exc.detail)


async def generic_exception_handler(request: fastapi.Request, exc: Exception):
    return build_error_response(
        status_code=500, title="Internal Server Error", detail="Something went wrong while processing your request."
    )


async def http_exception_handler(request: fastapi.Request, exc: starlette.exceptions.HTTPException):
    response = build_error_response(status_code=exc.status_code, title=exc.detail)
    headers = getattr(exc, "headers", None)
    if headers:
        response.init_headers(headers)

    return response


async def validation_error_handler(request: fastapi.Request, exc: fastapi.exceptions.RequestValidationError):
    detail = fastapi.encoders.jsonable_encoder(exc.errors())
    return build_error_response(status_code=422, title="Unprocessable Entity", detail=detail)
