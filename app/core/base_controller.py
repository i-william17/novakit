from typing import Any, Dict, List, Union, Optional, Generic, TypeVar
from fastapi.responses import JSONResponse
from pydantic import BaseModel



T = TypeVar('T')



class AlertifyPayload(BaseModel):
    message: str
    theme: str = "success"
    type: str = "alert"


class PaginationLinks(BaseModel):
    self: str
    first: Optional[str] = None
    last: Optional[str] = None
    next: Optional[str] = None
    prev: Optional[str] = None


class DataPayload(BaseModel, Generic[T]):
    data: Union[T, List[T], str]
    countOnPage: Optional[int] = None
    totalCount: Optional[int] = None
    perPage: Optional[int] = None
    totalPages: Optional[int] = None
    currentPage: Optional[int] = None
    paginationLinks: Optional[PaginationLinks] = None


class SuccessResponse(BaseModel, Generic[T]):
    # Both are optional.
    # If None, they are stripped from the final JSON by exclude_none=True
    dataPayload: Optional[DataPayload[T]] = None
    alertifyPayload: Optional[AlertifyPayload] = None


class ErrorPayload(BaseModel):
    errors: Union[List[str], Dict[str, Any], str]


class ErrorResponse(BaseModel):
    errorPayload: ErrorPayload




class BaseController:
    """
    Standardized Response Wrapper mimicking Yii2 logic.
    """

    def payload_response(
            self,
            data: Any,
            message: str = None,
            type: str = None,
            status_code: int = 200,
            one_record: bool = True,
            pagination: Dict = None
    ) -> JSONResponse:
        """
        Equivalent to Yii2: return $this->payloadResponse($model, ['message' => '...']);
        Returns: { "dataPayload": {...}, "alertifyPayload": {...} }
        """

        # --- A. Build DataPayload ---
        if one_record:
            payload_data = DataPayload(data=data)
        else:
            # Handle List / Pagination logic
            if not data or len(data) == 0:
                payload_data = DataPayload(
                    data="No records available",
                    countOnPage=0,
                    totalCount=0,
                    perPage=pagination.get("per_page", 25) if pagination else 25,
                    totalPages=0,
                    currentPage=pagination.get("page", 1) if pagination else 1,
                    paginationLinks=PaginationLinks(self=str(pagination.get("path", "/"))) if pagination else None
                )
            else:
                payload_data = DataPayload(
                    data=data,
                    countOnPage=len(data),
                    totalCount=pagination.get("total", len(data)) if pagination else len(data),
                    perPage=pagination.get("per_page", 25) if pagination else 25,
                    totalPages=pagination.get("total_pages", 1) if pagination else 1,
                    currentPage=pagination.get("page", 1) if pagination else 1,
                    paginationLinks=PaginationLinks(
                        self=str(pagination.get("path", "/")),
                        first=str(pagination.get("first_url")) if pagination else None,
                        last=str(pagination.get("last_url")) if pagination else None
                    ) if pagination else None
                )

        # --- B. Build AlertifyPayload (If message exists) ---
        alert_payload = None
        if message:
            alert_payload = AlertifyPayload(
                message=message,
                theme="success",
                type="alert"
            )

        # --- C. Combine & Return ---
        response_obj = SuccessResponse(
            dataPayload=payload_data,
            alertifyPayload=alert_payload
        )

        return JSONResponse(
            content=response_obj.model_dump(exclude_none=True),
            status_code=status_code
        )

    def alertify_response(
            self,
            message: str,
            theme: str = "success",
            type: str ="alert"
    ) -> JSONResponse:

        # 1. Create Alert
        alert_payload = AlertifyPayload(
            message=message,
            theme=theme,
            type= type
        )


        response_obj = SuccessResponse(
            alertifyPayload=alert_payload
        )


        return JSONResponse(
            content=response_obj.model_dump(exclude_none=True),

        )

    def error_response(
            self,
            errors: Union[str, Dict, List],
            status_code: int = 422,
            message: str = "Validation Error"
    ) -> JSONResponse:
        """
        Returns a standardized Error JSON.
        """
        response_obj = ErrorResponse(
            errorPayload=ErrorPayload(errors=errors)
        )

        return JSONResponse(
            content=response_obj.model_dump(),
            status_code=status_code
        )

    def format_pydantic_errors(self, pydantic_errors: List[Dict]) -> Dict[str, str]:
        """
        Transforms raw Pydantic errors into a simple Key:Message dictionary
        matching Yii2 style.

        Input:  [{'loc': ('body', 'smtp_port'), 'msg': 'Too big', 'type': '...'}]
        Output: {'smtp_port': 'Too big'}
        """
        formatted = {}
        for err in pydantic_errors:

            try:
                field = str(err["loc"][-1])
                message = err["msg"]
                formatted[field] = message
            except (IndexError, KeyError):

                formatted["general"] = err.get("msg", "Invalid Input")

        return formatted