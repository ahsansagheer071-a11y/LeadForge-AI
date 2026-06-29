from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import BaseAppException
from app.core.logging import logger
import traceback


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers global exception handlers for the FastAPI application.
    """

    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        """
        Handle custom domain-specific application exceptions.
        """
        logger.warning(
            f"Domain Exception: {exc.message} | Path: {request.url.path} | Status: {exc.status_code}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.__class__.__name__,
                    "message": exc.message,
                    "detail": exc.detail
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle request body or query parameter validation errors.
        """
        errors = []
        for error in exc.errors():
            errors.append({
                "loc": error.get("loc"),
                "msg": error.get("msg"),
                "type": error.get("type")
            })

        logger.warning(f"Validation Error: {errors} | Path: {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "RequestValidationError",
                    "message": "The request validation failed.",
                    "detail": errors
                }
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle all uncaught exceptions to prevent leakage of internal system details.
        """
        # Log the full traceback
        tb = traceback.format_exc()
        logger.error(
            f"Uncaught Exception: {str(exc)} | Path: {request.url.path}\nTraceback:\n{tb}"
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "InternalServerError",
                    "message": "An unexpected internal server error occurred. Please try again later.",
                    "detail": None
                }
            }
        )
