import os
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict, GetJsonSchemaHandler
from pydantic_core import CoreSchema, core_schema
from bson import ObjectId
from typing import List, Optional, Annotated, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Cloud Based To-Do List API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (important)
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    print("WARNING: MONGODB_URL environment variable not set. Please set it to your MongoDB Atlas connection string.")

client = AsyncIOMotorClient(MONGODB_URL)
db = client.todo_db
collection = db.tasks

# Helper to handle MongoDB ObjectId in Pydantic V2
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ]),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x), return_schema=core_schema.str_schema()
            ),
        )

    @classmethod
    def validate(cls, v: Any) -> ObjectId:
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> dict[str, Any]:
        return handler(core_schema.str_schema())

# Task Models
class TaskModel(BaseModel):
    id: Annotated[PyObjectId, Field(default_factory=PyObjectId, alias="_id")]
    title: str = Field(...)
    completed: bool = Field(default=False)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "title": "Buy groceries",
                "completed": False,
            }
        }
    )

class UpdateTaskModel(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

# Backend API Endpoints

@app.post("/tasks", response_description="Add new task", response_model=TaskModel)
async def create_task(task: TaskModel = Body(...)):
    new_task = await collection.insert_one(task.model_dump(by_alias=True, exclude={"id"}))
    created_task = await collection.find_one({"_id": new_task.inserted_id})
    return created_task

@app.get("/tasks", response_description="List all tasks", response_model=List[TaskModel])
async def list_tasks():
    tasks = await collection.find().to_list(1000)
    return tasks

@app.put("/tasks/{id}", response_description="Update a task", response_model=TaskModel)
async def update_task(id: str, task: UpdateTaskModel = Body(...)):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    update_data = {k: v for k, v in task.model_dump().items() if v is not None}
    
    if len(update_data) >= 1:
        update_result = await collection.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        if update_result.modified_count == 1:
            if (updated_task := await collection.find_one({"_id": ObjectId(id)})) is not None:
                return updated_task

    if (existing_task := await collection.find_one({"_id": ObjectId(id)})) is not None:
        return existing_task

    raise HTTPException(status_code=404, detail=f"Task {id} not found")

@app.delete("/tasks/{id}", response_description="Delete a task")
async def delete_task(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    delete_result = await collection.delete_one({"_id": ObjectId(id)})

    if delete_result.deleted_count == 1:
        return {"status": "success", "message": "Task deleted"}

    raise HTTPException(status_code=404, detail=f"Task {id} not found")

# Serve Frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<html><body><h1>Frontend index.html not found</h1></body></html>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
