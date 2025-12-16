"""
Dynamic Holiday Scanner Service.

This module provides automatic scanning and management of holidays
for current and future years with automatic cleanup of outdated holidays.
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Tuple
import calendar
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.leave import CorporateLeave
from ..models.user import User
from .corporate_leave import CorporateLeaveAIService


class HolidayScannerService:
    """
    Service for dynamic holiday scanning and management.
    
    This service automatically manages holidays for current year + 2 future years
    and removes outdated holidays from previous years.
    """
    
    @staticmethod
    def scan_and_update_holidays(
        db: Session, 
        admin_user: User,
        regions: List[str] = None,
        year_range: Tuple[int, int] = None
    ) -> Dict[str, Any]:
        """
        Scan and update holidays for specified year range.
        
        Args:
            db: Database session
            admin_user: Admin user performing the operation
            regions: List of regions to include (default: all supported)
            year_range: Tuple of (start_year, end_year) (default: current + 2 years)
            
        Returns:
            Dictionary with operation results
        """
        current_year = datetime.now().year
        
        # Default to current year + 2 future years if not specified
        if year_range is None:
            year_range = (current_year, current_year + 2)
        
        # Default regions if not specified
        if regions is None:
            regions = ["general", "india", "uk"]
        
        start_year, end_year = year_range
        
        # Clean up outdated holidays first
        cleanup_result = HolidayScannerService._cleanup_outdated_holidays(db, current_year)
        
        # Generate holidays for the specified range
        created_count = 0
        skipped_count = 0
        years_processed = []
        
        for year in range(start_year, end_year + 1):
            year_result = HolidayScannerService._process_year_holidays(db, admin_user, year, regions)
            created_count += year_result["created"]
            skipped_count += year_result["skipped"]
            years_processed.append(year)
        
        return {
            "message": "Holiday scan completed successfully",
            "year_range": f"{start_year}-{end_year}",
            "regions": regions,
            "created": created_count,
            "skipped": skipped_count,
            "years_processed": years_processed,
            "cleanup": cleanup_result
        }
    
    @staticmethod
    def scan_current_year_holidays(
        db: Session, 
        admin_user: User,
        regions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Scan and update holidays for current year only.
        
        Args:
            db: Database session
            admin_user: Admin user performing the operation
            regions: List of regions to include
            
        Returns:
            Dictionary with operation results
        """
        current_year = datetime.now().year
        return HolidayScannerService.scan_and_update_holidays(
            db, admin_user, regions, (current_year, current_year)
        )
    
    @staticmethod
    def scan_future_years_holidays(
        db: Session, 
        admin_user: User,
        regions: List[str] = None,
        years_ahead: int = 2
    ) -> Dict[str, Any]:
        """
        Scan and update holidays for current + future years.
        
        Args:
            db: Database session
            admin_user: Admin user performing the operation
            regions: List of regions to include
            years_ahead: Number of years ahead to scan
            
        Returns:
            Dictionary with operation results
        """
        current_year = datetime.now().year
        return HolidayScannerService.scan_and_update_holidays(
            db, admin_user, regions, (current_year, current_year + years_ahead)
        )
    
    @staticmethod
    def cleanup_old_holidays(
        db: Session,
        keep_years_back: int = 1
    ) -> Dict[str, Any]:
        """
        Clean up holidays from years before the specified threshold.
        
        Args:
            db: Database session
            keep_years_back: Number of years back to keep (default: 1)
            
        Returns:
            Dictionary with cleanup results
        """
        return HolidayScannerService._cleanup_outdated_holidays(db, datetime.now().year, keep_years_back)
    
    @staticmethod
    def _cleanup_outdated_holidays(
        db: Session, 
        current_year: int, 
        keep_years_back: int = 1
    ) -> Dict[str, Any]:
        """
        Remove holidays from years before the specified threshold.
        
        Args:
            db: Database session
            current_year: Current year
            keep_years_back: Number of years back to keep
            
        Returns:
            Dictionary with cleanup results
        """
        cutoff_year = current_year - keep_years_back
        
        # Find holidays to delete
        old_holidays = db.query(CorporateLeave).filter(
            CorporateLeave.date < date(cutoff_year, 1, 1)
        ).all()
        
        deleted_count = 0
        deleted_details = []
        
        for holiday in old_holidays:
            deleted_details.append({
                "name": holiday.name,
                "date": holiday.date,
                "type": holiday.leave_type
            })
            db.delete(holiday)
            deleted_count += 1
        
        if deleted_count > 0:
            db.commit()
        
        return {
            "deleted_count": deleted_count,
            "cutoff_year": cutoff_year,
            "deleted_holidays": deleted_details
        }
    
    @staticmethod
    def _process_year_holidays(
        db: Session,
        admin_user: User,
        year: int,
        regions: List[str]
    ) -> Dict[str, Any]:
        """
        Process holidays for a specific year and regions.
        
        Args:
            db: Database session
            admin_user: Admin user
            year: Year to process
            regions: List of regions
            
        Returns:
            Dictionary with processing results
        """
        created_count = 0
        skipped_count = 0
        
        for region in regions:
            # Generate holidays for this region and year
            generated_leaves = CorporateLeaveAIService.generate_corporate_leaves(year, region)
            
            for leave_data in generated_leaves:
                # Check if a corporate leave with same date already exists
                existing_leave = db.query(CorporateLeave).filter(
                    and_(
                        CorporateLeave.date == leave_data["date"],
                        CorporateLeave.name == leave_data["name"]
                    )
                ).first()
                
                if not existing_leave:
                    # Create new corporate leave
                    corporate_leave = CorporateLeave(
                        name=leave_data["name"],
                        date=leave_data["date"],
                        leave_type=leave_data["type"],
                        is_recurring=str(leave_data["is_recurring"]).lower(),
                        created_by=admin_user.id
                    )
                    db.add(corporate_leave)
                    created_count += 1
                else:
                    skipped_count += 1
        
        if created_count > 0:
            db.commit()
        
        return {
            "year": year,
            "regions": regions,
            "created": created_count,
            "skipped": skipped_count
        }
    
    @staticmethod
    def get_holiday_statistics(db: Session) -> Dict[str, Any]:
        """
        Get statistics about current holidays in the database.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with holiday statistics
        """
        current_year = datetime.now().year
        
        # Get holidays by year
        all_holidays = db.query(CorporateLeave).all()
        
        years_stats = {}
        type_stats = {}
        total_count = len(all_holidays)
        
        for holiday in all_holidays:
            year = holiday.date.year
            leave_type = holiday.leave_type
            
            # Count by year
            if year not in years_stats:
                years_stats[year] = 0
            years_stats[year] += 1
            
            # Count by type
            if leave_type not in type_stats:
                type_stats[leave_type] = 0
            type_stats[leave_type] += 1
        
        return {
            "total_holidays": total_count,
            "years_with_holidays": list(years_stats.keys()),
            "holidays_by_year": years_stats,
            "holidays_by_type": type_stats,
            "current_year": current_year,
            "is_current_year_scanned": current_year in years_stats
        }
    
    @staticmethod
    def detect_holiday_conflicts(db: Session, year: int = None) -> List[Dict[str, Any]]:
        """
        Detect potential holiday conflicts in the database.
        
        Args:
            db: Database session
            year: Optional year to filter conflicts
            
        Returns:
            List of potential conflicts
        """
        query = db.query(CorporateLeave)
        
        if year:
            query = query.filter(
                and_(
                    CorporateLeave.date >= date(year, 1, 1),
                    CorporateLeave.date <= date(year, 12, 31)
                )
            )
        
        holidays = query.order_by(CorporateLeave.date).all()
        
        conflicts = []
        
        for i in range(len(holidays) - 1):
            current_holiday = holidays[i]
            next_holiday = holidays[i + 1]
            
            # Check if holidays are within 1 day of each other
            date_diff = (next_holiday.date - current_holiday.date).days
            
            if date_diff <= 1:
                conflicts.append({
                    "holiday1": {
                        "name": current_holiday.name,
                        "date": current_holiday.date,
                        "type": current_holiday.leave_type
                    },
                    "holiday2": {
                        "name": next_holiday.name,
                        "date": next_holiday.date,
                        "type": next_holiday.leave_type
                    },
                    "days_apart": date_diff,
                    "severity": "high" if date_diff == 0 else "medium"
                })
        
        return conflicts
