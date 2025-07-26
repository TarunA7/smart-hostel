from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

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

class UserRole(str, Enum):
    STUDENT = "student"
    WARDEN = "warden"

# Auth Models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole
    full_name: str
    phone: Optional[str] = None
    student_id: Optional[str] = None  # Only for students

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    role: UserRole
    full_name: str
    phone: Optional[str] = None
    student_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Existing Models
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

# Authentication Helpers
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user(username: str) -> Optional[UserInDB]:
    user_data = await db.users.find_one({"username": username})
    if user_data:
        return UserInDB(**user_data)
    return None

async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = await get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    user = await get_user(username)
    if user is None:
        raise credentials_exception
    return User(**user.dict())

async def get_current_warden(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.WARDEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_current_student(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Authentication Routes
@api_router.post("/auth/register", response_model=Token)
async def register_user(user: UserCreate):
    # Check if user already exists
    existing_user = await get_user(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await db.users.find_one({"email": user.email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user.password)
    user_dict = user.dict()
    del user_dict['password']
    user_in_db = UserInDB(**user_dict, hashed_password=hashed_password)
    
    await db.users.insert_one(user_in_db.dict())
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=User(**user_dict)
    )

@api_router.post("/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    user = await authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=User(**user.dict())
    )

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Student Management Routes (Warden only for create/update/delete, Students can view their own data)
@api_router.post("/students", response_model=Student)
async def create_student(student: StudentCreate, current_user: User = Depends(get_current_warden)):
    student_dict = student.dict()
    student_obj = Student(**student_dict)
    await db.students.insert_one(student_obj.dict())
    return student_obj

@api_router.get("/students", response_model=List[Student])
async def get_students(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.STUDENT:
        # Students can only see their own data
        students = await db.students.find({"student_id": current_user.student_id}).to_list(1000)
    else:
        # Wardens can see all students
        students = await db.students.find().to_list(1000)
    return [Student(**student) for student in students]

@api_router.get("/students/{student_id}", response_model=Student)
async def get_student(student_id: str, current_user: User = Depends(get_current_user)):
    student = await db.students.find_one({"id": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student_obj = Student(**student)
    
    # Students can only view their own data
    if current_user.role == UserRole.STUDENT and student_obj.student_id != current_user.student_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return student_obj

@api_router.put("/students/{student_id}", response_model=Student)
async def update_student(student_id: str, student_update: StudentUpdate, current_user: User = Depends(get_current_warden)):
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
async def delete_student(student_id: str, current_user: User = Depends(get_current_warden)):
    result = await db.students.delete_one({"id": student_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted successfully"}

# Room Management Routes (Warden only)
@api_router.post("/rooms", response_model=Room)
async def create_room(room: RoomCreate, current_user: User = Depends(get_current_warden)):
    room_dict = room.dict()
    room_obj = Room(**room_dict)
    await db.rooms.insert_one(room_obj.dict())
    return room_obj

@api_router.get("/rooms", response_model=List[Room])
async def get_rooms(current_user: User = Depends(get_current_user)):
    rooms = await db.rooms.find().to_list(1000)
    return [Room(**room) for room in rooms]

@api_router.get("/rooms/available", response_model=List[Room])
async def get_available_rooms(current_user: User = Depends(get_current_user)):
    rooms = await db.rooms.find({"status": RoomStatus.AVAILABLE, "occupied": {"$lt": "$capacity"}}).to_list(1000)
    return [Room(**room) for room in rooms]

@api_router.post("/rooms/{room_id}/allocate/{student_id}")
async def allocate_room(room_id: str, student_id: str, current_user: User = Depends(get_current_warden)):
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

# Visitor Management Routes (Warden only)
@api_router.post("/visitors", response_model=Visitor)
async def create_visitor(visitor: VisitorCreate, current_user: User = Depends(get_current_warden)):
    visitor_dict = visitor.dict()
    visitor_obj = Visitor(**visitor_dict)
    await db.visitors.insert_one(visitor_obj.dict())
    return visitor_obj

@api_router.get("/visitors", response_model=List[Visitor])
async def get_visitors(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.STUDENT:
        # Students can only see visitors visiting them
        visitors = await db.visitors.find({"visiting_student_id": current_user.student_id}).to_list(1000)
    else:
        # Wardens can see all visitors
        visitors = await db.visitors.find().to_list(1000)
    return [Visitor(**visitor) for visitor in visitors]

@api_router.get("/visitors/active", response_model=List[Visitor])
async def get_active_visitors(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.STUDENT:
        visitors = await db.visitors.find({"status": "checked_in", "visiting_student_id": current_user.student_id}).to_list(1000)
    else:
        visitors = await db.visitors.find({"status": "checked_in"}).to_list(1000)
    return [Visitor(**visitor) for visitor in visitors]

@api_router.post("/visitors/{visitor_id}/checkout")
async def checkout_visitor(visitor_id: str, current_user: User = Depends(get_current_warden)):
    result = await db.visitors.update_one(
        {"id": visitor_id},
        {"$set": {"check_out": datetime.utcnow(), "status": "checked_out"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Visitor not found")
    return {"message": "Visitor checked out successfully"}

# Maintenance Request Routes (Students can create, Wardens can manage)
@api_router.post("/maintenance", response_model=MaintenanceRequest)
async def create_maintenance_request(request: MaintenanceRequestCreate, current_user: User = Depends(get_current_user)):
    request_dict = request.dict()
    request_obj = MaintenanceRequest(**request_dict)
    await db.maintenance_requests.insert_one(request_obj.dict())
    return request_obj

@api_router.get("/maintenance", response_model=List[MaintenanceRequest])
async def get_maintenance_requests(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.STUDENT:
        # Students can only see their own requests
        requests = await db.maintenance_requests.find({"student_id": current_user.student_id}).to_list(1000)
    else:
        # Wardens can see all requests
        requests = await db.maintenance_requests.find().to_list(1000)
    return [MaintenanceRequest(**request) for request in requests]

@api_router.put("/maintenance/{request_id}/status")
async def update_maintenance_status(request_id: str, status: RequestStatus, current_user: User = Depends(get_current_warden)):
    result = await db.maintenance_requests.update_one(
        {"id": request_id},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"message": "Status updated successfully"}

# Fee Management Routes (Warden only for create/update, Students can view their own fees)
@api_router.post("/fees", response_model=FeeRecord)
async def create_fee_record(fee: FeeRecordCreate, current_user: User = Depends(get_current_warden)):
    fee_dict = fee.dict()
    fee_obj = FeeRecord(**fee_dict)
    await db.fee_records.insert_one(fee_obj.dict())
    return fee_obj

@api_router.get("/fees", response_model=List[FeeRecord])
async def get_fee_records(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.STUDENT:
        # Students can only see their own fees
        fees = await db.fee_records.find({"student_id": current_user.student_id}).to_list(1000)
    else:
        # Wardens can see all fees
        fees = await db.fee_records.find().to_list(1000)
    return [FeeRecord(**fee) for fee in fees]

@api_router.get("/fees/overdue", response_model=List[FeeRecord])
async def get_overdue_fees(current_user: User = Depends(get_current_user)):
    current_date = datetime.utcnow()
    if current_user.role == UserRole.STUDENT:
        fees = await db.fee_records.find({
            "student_id": current_user.student_id,
            "due_date": {"$lt": current_date},
            "status": {"$ne": FeeStatus.PAID}
        }).to_list(1000)
    else:
        fees = await db.fee_records.find({
            "due_date": {"$lt": current_date},
            "status": {"$ne": FeeStatus.PAID}
        }).to_list(1000)
    return [FeeRecord(**fee) for fee in fees]

@api_router.post("/fees/{fee_id}/pay")
async def pay_fee(fee_id: str, current_user: User = Depends(get_current_warden)):
    result = await db.fee_records.update_one(
        {"id": fee_id},
        {"$set": {"status": FeeStatus.PAID, "paid_date": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Fee record not found")
    return {"message": "Fee paid successfully"}

# Movement/In-Out Tracking Routes (Warden only for logging, Students can view their own movements)
@api_router.post("/movements", response_model=MovementLog)
async def log_movement(movement: MovementLogCreate, current_user: User = Depends(get_current_warden)):
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
async def get_movements(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.STUDENT:
        # Students can only see their own movements
        movements = await db.movement_logs.find({"student_id": current_user.student_id}).sort("timestamp", -1).to_list(1000)
    else:
        # Wardens can see all movements
        movements = await db.movement_logs.find().sort("timestamp", -1).to_list(1000)
    return [MovementLog(**movement) for movement in movements]

@api_router.get("/movements/recent", response_model=List[MovementLog])
async def get_recent_movements(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.STUDENT:
        movements = await db.movement_logs.find({"student_id": current_user.student_id}).sort("timestamp", -1).limit(50).to_list(50)
    else:
        movements = await db.movement_logs.find().sort("timestamp", -1).limit(50).to_list(50)
    return [MovementLog(**movement) for movement in movements]

# Dashboard Stats Route (Both roles with filtered data)
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.STUDENT:
        # Students see limited stats
        student_data = await db.students.find_one({"student_id": current_user.student_id})
        if not student_data:
            raise HTTPException(status_code=404, detail="Student record not found")
        
        # Get student's room info
        room_data = await db.rooms.find_one({"room_number": student_data.get("room_number")})
        
        # Get student's fees
        overdue_fees = await db.fee_records.count_documents({
            "student_id": current_user.student_id,
            "due_date": {"$lt": datetime.utcnow()},
            "status": {"$ne": FeeStatus.PAID}
        })
        
        # Get student's maintenance requests
        pending_maintenance = await db.maintenance_requests.count_documents({
            "student_id": current_user.student_id,
            "status": RequestStatus.PENDING
        })
        
        # Get student's visitors
        active_visitors = await db.visitors.count_documents({
            "visiting_student_id": current_user.student_id,
            "status": "checked_in"
        })
        
        return DashboardStats(
            total_students=1,
            students_in=1 if student_data.get("status") == "in" else 0,
            students_out=1 if student_data.get("status") == "out" else 0,
            total_rooms=1 if room_data else 0,
            occupied_rooms=1 if room_data and room_data.get("occupied", 0) > 0 else 0,
            available_rooms=0,
            maintenance_rooms=0,
            pending_maintenance=pending_maintenance,
            overdue_fees=overdue_fees,
            active_visitors=active_visitors
        )
    else:
        # Wardens see all stats
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