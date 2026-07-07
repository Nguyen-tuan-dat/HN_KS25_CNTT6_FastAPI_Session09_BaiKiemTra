from fastapi import FastAPI, status, Request, HTTPException
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

courses_db = [
    {"id": 1, "course_name": "FastAPI Masterclass", "duration_hours": 32, "price": 1500000, "status": "active", "created_at": "2026-07-01T02:00:00Z"},
    {"id": 2, "course_name": "NextJS Next-Level", "duration_hours": 45, "price": 1800000, "status": "active", "created_at": "2026-07-01T03:15:00Z"}
]

app = FastAPI()

class CreateCourse(BaseModel):
    course_name: str = Field(min_length=5)
    duration_hours: int = Field(gt=0)
    price: int = Field(ge=0)

class BaseResponse(BaseModel):
    status_code: int
    message: str
    data: Optional[Any]
    errors: Optional[Any]
    timestamp: str
    path: str
    
def create_response(req: Request, status_code: int, message: str, data = None, errors = None):
    return BaseResponse(
        status_code= status_code,
        message= message,
        data = data,
        errors = errors,
        timestamp= datetime.now().isoformat(),
        path = req.url.path
    )
    
@app.get("/courses")
def get_all_courses(request: Request):
    return create_response(request, status.HTTP_200_OK,"Lấy danh sách khóa học thành công!",courses_db)

@app.post("/courses")
def create_course(request: Request, new_course: CreateCourse):
    for course in courses_db:
        if course["course_name"].lower() == new_course.course_name.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ERR-EDU-01: Course name duplicates an existing record in memory array."
            )
    new_id = max(course["id"] for course in courses_db) + 1
    course = {
        "id": new_id,
        "course_name": new_course.course_name,
        "duration_hours": new_course.duration_hours,
        "price": new_course.price,
        "status": "active",
        "created_at": datetime.now().isoformat() + "Z"
    }
    courses_db.append(course)
    return create_response(request, status.HTTP_201_CREATED, "Tạo mới khóa học thành công!",course)   
  
@app.delete("/courses/{course_id}")
def delete_course(request: Request, course_id: int):
    for course in courses_db:
        if course["id"] == course_id:
            courses_db.remove(course)
            return create_response(request, status.HTTP_200_OK, "Xóa khóa học thành công!")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="ERR-EDU-02: Target course ID can not be found."
    )

@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 400:
        message = "Lỗi: Tên khóa học này đã tồn tại trong danh mục đào tạo!"
    elif exc.status_code == 404:
        message = "Lỗi: Không tìm thấy mã khóa học yêu cầu để xóa!"
    else:
        message = "Failed!"
    response = create_response(request, exc.status_code, "Failed!", errors=exc.detail)
    return JSONResponse(
        content=response.model_dump(),
        status_code=response.status_code
    )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(type(exc))
    response = create_response(request,status.HTTP_422_UNPROCESSABLE_ENTITY,"Dữ liệu đầu vào không hợp lệ!",errors=exc.errors())
    return JSONResponse(
        content=response.model_dump(),
        status_code=response.status_code
    )

@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    response = create_response(request, status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed", errors = str(exc))
    return JSONResponse(
        content = response.model_dump(),
        status_code = response.status_code
    )