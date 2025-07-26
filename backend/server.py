from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class RoomStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"

class StudentStatus(str, Enum):
    IN = "in"
    OUT = "out"

class RequestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class FeeStatus(str, Enum):
    PAID = "paid"
    PENDING = "pending"
    OVERDUE = "overdue"

# Models
class Student(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: str
    student_id: str
    room_number: Optional[str] = None
    status: StudentStatus = StudentStatus.IN
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)

class StudentCreate(BaseModel):
    name: str
    email: str
    phone: str
    student_id: str

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    room_number: Optional[str] = None
    status: Optional[StudentStatus] = None

class Room(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_number: str
    floor: int
    capacity: int
    occupied: int = 0
    status: RoomStatus = RoomStatus.AVAILABLE
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RoomCreate(BaseModel):
    room_number: str
    floor: int
    capacity: int

class Visitor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: str
    visiting_student_id: str
    visiting_student_name: str
    purpose: str
    check_in: datetime = Field(default_factory=datetime.utcnow)
    check_out: Optional[datetime] = None
    status: str = "checked_in"

class VisitorCreate(BaseModel):
    name: str
    phone: str
    visiting_student_id: str
    visiting_student_name: str
    purpose: str

class MaintenanceRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    student_name: str
    room_number: str
    issue_type: str
    description: str
    status: RequestStatus = RequestStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MaintenanceRequestCreate(BaseModel):
    student_id: str
    student_name: str
    room_number: str
    issue_type: str
    description: str

class FeeRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    student_name: str
    fee_type: str
    amount: float
    due_date: datetime
    status: FeeStatus = FeeStatus.PENDING
    paid_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FeeRecordCreate(BaseModel):
    student_id: str
    student_name: str
    fee_type: str
    amount: float
    due_date: datetime

class MovementLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    student_name: str
    action: str  # "check_in" or "check_out"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    note: Optional[str] = None

class MovementLogCreate(BaseModel):
    student_id: str
    student_name: str
    action: str
    note: Optional[str] = None

# Dashboard Stats
class DashboardStats(BaseModel):
    total_students: int
    students_in: int
    students_out: int
    total_rooms: int
    occupied_rooms: int
    available_rooms: int
    maintenance_rooms: int
    pending_maintenance: int
    overdue_fees: int
    active_visitors: int

# Student Management Routes
@api_router.post("/students", response_model=Student)
async def create_student(student: StudentCreate):
    student_dict = student.dict()
    student_obj = Student(**student_dict)
    await db.students.insert_one(student_obj.dict())
    return student_obj

@api_router.get("/students", response_model=List[Student])
async def get_students():
    students = await db.students.find().to_list(1000)
    return [Student(**student) for student in students]

@api_router.get("/students/{student_id}", response_model=Student)
async def get_student(student_id: str):
    student = await db.students.find_one({"id": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return Student(**student)

@api_router.put("/students/{student_id}", response_model=Student)
async def update_student(student_id: str, student_update: StudentUpdate):
    update_data = {k: v for k, v in student_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    result = await db.students.update_one(
        {"id": student_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = await db.students.find_one({"id": student_id})
    return Student(**student)

@api_router.delete("/students/{student_id}")
async def delete_student(student_id: str):
    result = await db.students.delete_one({"id": student_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted successfully"}

# Room Management Routes
@api_router.post("/rooms", response_model=Room)
async def create_room(room: RoomCreate):
    room_dict = room.dict()
    room_obj = Room(**room_dict)
    await db.rooms.insert_one(room_obj.dict())
    return room_obj

@api_router.get("/rooms", response_model=List[Room])
async def get_rooms():
    rooms = await db.rooms.find().to_list(1000)
    return [Room(**room) for room in rooms]

@api_router.get("/rooms/available", response_model=List[Room])
async def get_available_rooms():
    rooms = await db.rooms.find({"status": RoomStatus.AVAILABLE, "occupied": {"$lt": "$capacity"}}).to_list(1000)
    return [Room(**room) for room in rooms]

@api_router.post("/rooms/{room_id}/allocate/{student_id}")
async def allocate_room(room_id: str, student_id: str):
    # Check if room exists and is available
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room_obj = Room(**room)
    if room_obj.occupied >= room_obj.capacity:
        raise HTTPException(status_code=400, detail="Room is full")
    
    # Check if student exists
    student = await db.students.find_one({"id": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update student's room
    await db.students.update_one(
        {"id": student_id},
        {"$set": {"room_number": room_obj.room_number}}
    )
    
    # Update room occupancy
    new_occupied = room_obj.occupied + 1
    new_status = RoomStatus.OCCUPIED if new_occupied >= room_obj.capacity else RoomStatus.AVAILABLE
    
    await db.rooms.update_one(
        {"id": room_id},
        {"$set": {"occupied": new_occupied, "status": new_status}}
    )
    
    return {"message": "Room allocated successfully"}

# Visitor Management Routes
@api_router.post("/visitors", response_model=Visitor)
async def create_visitor(visitor: VisitorCreate):
    visitor_dict = visitor.dict()
    visitor_obj = Visitor(**visitor_dict)
    await db.visitors.insert_one(visitor_obj.dict())
    return visitor_obj

@api_router.get("/visitors", response_model=List[Visitor])
async def get_visitors():
    visitors = await db.visitors.find().to_list(1000)
    return [Visitor(**visitor) for visitor in visitors]

@api_router.get("/visitors/active", response_model=List[Visitor])
async def get_active_visitors():
    visitors = await db.visitors.find({"status": "checked_in"}).to_list(1000)
    return [Visitor(**visitor) for visitor in visitors]

@api_router.post("/visitors/{visitor_id}/checkout")
async def checkout_visitor(visitor_id: str):
    result = await db.visitors.update_one(
        {"id": visitor_id},
        {"$set": {"check_out": datetime.utcnow(), "status": "checked_out"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Visitor not found")
    return {"message": "Visitor checked out successfully"}

# Maintenance Request Routes
@api_router.post("/maintenance", response_model=MaintenanceRequest)
async def create_maintenance_request(request: MaintenanceRequestCreate):
    request_dict = request.dict()
    request_obj = MaintenanceRequest(**request_dict)
    await db.maintenance_requests.insert_one(request_obj.dict())
    return request_obj

@api_router.get("/maintenance", response_model=List[MaintenanceRequest])
async def get_maintenance_requests():
    requests = await db.maintenance_requests.find().to_list(1000)
    return [MaintenanceRequest(**request) for request in requests]

@api_router.put("/maintenance/{request_id}/status")
async def update_maintenance_status(request_id: str, status: RequestStatus):
    result = await db.maintenance_requests.update_one(
        {"id": request_id},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"message": "Status updated successfully"}

# Fee Management Routes
@api_router.post("/fees", response_model=FeeRecord)
async def create_fee_record(fee: FeeRecordCreate):
    fee_dict = fee.dict()
    fee_obj = FeeRecord(**fee_dict)
    await db.fee_records.insert_one(fee_obj.dict())
    return fee_obj

@api_router.get("/fees", response_model=List[FeeRecord])
async def get_fee_records():
    fees = await db.fee_records.find().to_list(1000)
    return [FeeRecord(**fee) for fee in fees]

@api_router.get("/fees/overdue", response_model=List[FeeRecord])
async def get_overdue_fees():
    current_date = datetime.utcnow()
    fees = await db.fee_records.find({
        "due_date": {"$lt": current_date},
        "status": {"$ne": FeeStatus.PAID}
    }).to_list(1000)
    return [FeeRecord(**fee) for fee in fees]

@api_router.post("/fees/{fee_id}/pay")
async def pay_fee(fee_id: str):
    result = await db.fee_records.update_one(
        {"id": fee_id},
        {"$set": {"status": FeeStatus.PAID, "paid_date": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Fee record not found")
    return {"message": "Fee paid successfully"}

# Movement/In-Out Tracking Routes
@api_router.post("/movements", response_model=MovementLog)
async def log_movement(movement: MovementLogCreate):
    movement_dict = movement.dict()
    movement_obj = MovementLog(**movement_dict)
    await db.movement_logs.insert_one(movement_obj.dict())
    
    # Update student status
    new_status = StudentStatus.IN if movement.action == "check_in" else StudentStatus.OUT
    await db.students.update_one(
        {"id": movement.student_id},
        {"$set": {"status": new_status, "last_seen": datetime.utcnow()}}
    )
    
    return movement_obj

@api_router.get("/movements", response_model=List[MovementLog])
async def get_movements():
    movements = await db.movement_logs.find().sort("timestamp", -1).to_list(1000)
    return [MovementLog(**movement) for movement in movements]

@api_router.get("/movements/recent", response_model=List[MovementLog])
async def get_recent_movements():
    movements = await db.movement_logs.find().sort("timestamp", -1).limit(50).to_list(50)
    return [MovementLog(**movement) for movement in movements]

# Dashboard Stats Route
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    # Get student stats
    total_students = await db.students.count_documents({})
    students_in = await db.students.count_documents({"status": StudentStatus.IN})
    students_out = await db.students.count_documents({"status": StudentStatus.OUT})
    
    # Get room stats
    total_rooms = await db.rooms.count_documents({})
    occupied_rooms = await db.rooms.count_documents({"status": RoomStatus.OCCUPIED})
    available_rooms = await db.rooms.count_documents({"status": RoomStatus.AVAILABLE})
    maintenance_rooms = await db.rooms.count_documents({"status": RoomStatus.MAINTENANCE})
    
    # Get maintenance stats
    pending_maintenance = await db.maintenance_requests.count_documents({"status": RequestStatus.PENDING})
    
    # Get fee stats
    current_date = datetime.utcnow()
    overdue_fees = await db.fee_records.count_documents({
        "due_date": {"$lt": current_date},
        "status": {"$ne": FeeStatus.PAID}
    })
    
    # Get visitor stats
    active_visitors = await db.visitors.count_documents({"status": "checked_in"})
    
    return DashboardStats(
        total_students=total_students,
        students_in=students_in,
        students_out=students_out,
        total_rooms=total_rooms,
        occupied_rooms=occupied_rooms,
        available_rooms=available_rooms,
        maintenance_rooms=maintenance_rooms,
        pending_maintenance=pending_maintenance,
        overdue_fees=overdue_fees,
        active_visitors=active_visitors
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()