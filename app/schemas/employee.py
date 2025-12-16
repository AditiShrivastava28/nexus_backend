
"""
Employee-related Pydantic schemas.

This module defines schemas for employee profile and job history operations.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class EmployeeJobBase(BaseModel):
    """
    Base schema for employee job history.
    
    Attributes:
        company: Company name
        designation: Job title
        start_date: Start date
        end_date: End date
        description: Job description
    """
    company: str
    designation: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


class EmployeeJobCreate(EmployeeJobBase):
    """Schema for creating a job entry."""
    pass


class EmployeeJobResponse(EmployeeJobBase):
    """
    Job entry response schema.
    
    Attributes:
        id: Job entry ID
    """
    id: int

    class Config:
        from_attributes = True


class EmployeeProfileUpdate(BaseModel):
    """
    Schema for updating employee profile.
    
    Attributes:
        dob: Date of birth
        gender: Gender
        marital_status: Marital status
        blood_group: Blood group
        address: Residential address
        personal_email: Personal email
        mobile: Mobile phone number
    """
    dob: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    personal_email: Optional[str] = None
    mobile: Optional[str] = None



class ManagerInfo(BaseModel):
    """
    Manager information for employee responses.
    
    Attributes:
        id: Manager's employee ID
        employeeId: Manager's company employee ID

        email: Manager's work email
        designation: Manager's job title
        department: Manager's department
    """
    id: int
    employeeId: str
    name: str
    email: str
    designation: Optional[str] = None
    department: Optional[str] = None

    class Config:
        from_attributes = True


class EmployeeProfile(BaseModel):
    """
    Full employee profile response.
    
    Attributes:
        id: Employee ID (internal)
        employeeId: Company employee ID
        name: Full name
        email: Work email
        department: Department
        designation: Job title
        joinDate: Date of joining
        location: Work location
        manager: Manager employee object (null if no manager assigned)
        dob: Date of birth
        gender: Gender
        marital_status: Marital status
        blood_group: Blood group
        address: Address
        personal_email: Personal email
        mobile: Mobile number
        avatar_url: Profile picture URL
        status: Employment status
    """
    id: int
    employeeId: str
    name: str
    email: str
    department: Optional[str] = None
    designation: Optional[str] = None
    joinDate: Optional[date] = None
    location: Optional[str] = None
    manager: Optional[ManagerInfo] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    personal_email: Optional[str] = None
    mobile: Optional[str] = None
    avatar_url: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

class EmployeeListItem(BaseModel):
    """
    Employee item for list views.
    
    Attributes:
        id: Employee ID
        name: Full name
        role: Job title
        department: Department
        salary: Monthly salary
        email: Work email
        status: Employment status
        avatar: Profile picture URL
        joinDate: Date of joining
        location: Work location
        manager: Manager name
    """
    id: int
    name: str
    role: Optional[str] = None
    department: Optional[str] = None
    salary: Optional[float] = None
    email: str
    status: Optional[str] = None
    avatar: Optional[str] = None
    joinDate: Optional[date] = None
    location: Optional[str] = None
    manager: Optional[str] = None

    class Config:
        from_attributes = True



class EmployeeCreate(BaseModel):
    """
    Schema for creating a new employee.
    
    Attributes:
        email: Work email
        password: Initial password
        full_name: Full name
        employee_id: Company employee ID (optional, auto-generated if not provided)
        department: Department
        designation: Job title
        join_date: Date of joining
        location: Work location
        manager_id: Manager's employee ID
        role: User role (admin, manager, employee)
    """
    email: str
    password: str
    full_name: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    join_date: Optional[date] = None
    location: Optional[str] = None
    manager_id: Optional[int] = None
    role: str = "employee"


class EmployeeUpdate(BaseModel):
    """
    Schema for updating employee information.
    
    Attributes:
        full_name: Full name
        department: Department
        designation: Job title
        location: Work location
        manager_id: Manager's employee ID
        status: Employment status
    """
    full_name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    manager_id: Optional[int] = None
    status: Optional[str] = None


class EmployeeStatusUpdate(BaseModel):
    """
    Schema for updating employee status.
    
    Attributes:
        status: New employment status
    """
    status: str


class TeamMemberResponse(BaseModel):
    """
    Team member response for team view.
    
    Attributes:
        id: Employee ID
        name: Full name
        role: Job title
        status: Employment status
        location: Work location
        img: Profile picture URL
        isOnline: Whether currently online
    """
    id: int
    name: str
    role: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    img: Optional[str] = None

    isOnline: bool = False

    class Config:
        from_attributes = True


class TeammateResponse(BaseModel):
    """
    Detailed team member response for teammates page.
    
    Attributes:
        id: Employee ID
        name: Full name
        designation: Job title
        department: Department
        join_date: Date of joining
        status: Employment status
        location: Work location
        avatar_url: Profile picture URL
        email: Work email
        mobile: Mobile number
    """
    id: int
    name: str
    designation: Optional[str] = None
    department: Optional[str] = None
    join_date: Optional[date] = None
    status: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None
    email: str
    mobile: Optional[str] = None

    class Config:
        from_attributes = True

