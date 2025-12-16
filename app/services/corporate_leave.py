"""
Corporate Leave AI Service.

This module provides AI-powered generation of corporate holidays and official leaves.
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any
import calendar


class CorporateLeaveAIService:
    """
    Service for generating AI-powered corporate leave calendar.
    
    This service generates common corporate holidays and official leaves
    for a given year based on standard corporate calendar practices.
    """
    

    @staticmethod
    def generate_corporate_leaves(year: int, region: str = "general") -> List[Dict[str, Any]]:
        """
        Generate AI-based corporate leaves for a given year.
        
        Args:
            year: Year for which to generate corporate leaves
            region: Region/country for specific holidays (default: general)
            
        Returns:
            List of dictionaries containing leave information
        """
        corporate_leaves = []
        
        # Fixed date holidays (same date every year)
        fixed_holidays = [
            {
                "name": "New Year's Day",
                "month": 1,
                "day": 1,
                "type": "National Holiday",
                "description": "Celebration of New Year"
            },
            {
                "name": "Independence Day",
                "month": 7,
                "day": 4,
                "type": "National Holiday",
                "description": "Independence Day celebration"
            },
            {
                "name": "Christmas Day",
                "month": 12,
                "day": 25,
                "type": "National Holiday",
                "description": "Christmas celebration"
            },
            {
                "name": "New Year's Eve",
                "month": 12,
                "day": 31,
                "type": "Corporate Holiday",
                "description": "End of year celebration"
            }
        ]
        
        # Add fixed holidays
        for holiday in fixed_holidays:
            holiday_date = date(year, holiday["month"], holiday["day"])
            
            # Skip if date doesn't exist (e.g., February 30th)
            try:
                corporate_leaves.append({
                    "date": holiday_date,
                    "name": holiday["name"],
                    "type": holiday["type"],
                    "is_recurring": True,
                    "description": holiday["description"]
                })
            except ValueError:
                continue
        
        # Floating holidays (different days each year)
        floating_holidays = CorporateLeaveAIService._generate_floating_holidays(year)
        corporate_leaves.extend(floating_holidays)
        
        # Corporate-specific holidays
        corporate_specific = CorporateLeaveAIService._generate_corporate_specific_holidays(year)
        corporate_leaves.extend(corporate_specific)
        
        # Religious and cultural festivals
        religious_festivals = CorporateLeaveAIService.generate_religious_festivals(year, region)
        corporate_leaves.extend(religious_festivals)
        
        return corporate_leaves
    
    @staticmethod
    def _generate_floating_holidays(year: int) -> List[Dict[str, Any]]:
        """
        Generate floating holidays that change date each year.
        
        Args:
            year: Year for which to generate floating holidays
            
        Returns:
            List of floating holiday dictionaries
        """
        floating_holidays = []
        
        # Martin Luther King Jr. Day (3rd Monday in January)
        mlk_day = CorporateLeaveAIService._get_nth_weekday_of_month(year, 1, 0, 3)  # 0 = Monday
        if mlk_day:
            floating_holidays.append({
                "date": mlk_day,
                "name": "Martin Luther King Jr. Day",
                "type": "Federal Holiday",
                "is_recurring": True,
                "description": "Birthday of Martin Luther King Jr."
            })
        
        # Presidents' Day (3rd Monday in February)
        presidents_day = CorporateLeaveAIService._get_nth_weekday_of_month(year, 2, 0, 3)
        if presidents_day:
            floating_holidays.append({
                "date": presidents_day,
                "name": "Presidents' Day",
                "type": "Federal Holiday",
                "is_recurring": True,
                "description": "Washington's Birthday"
            })
        
        # Memorial Day (Last Monday in May)
        memorial_day = CorporateLeaveAIService._get_last_weekday_of_month(year, 5, 0)
        if memorial_day:
            floating_holidays.append({
                "date": memorial_day,
                "name": "Memorial Day",
                "type": "Federal Holiday",
                "is_recurring": True,
                "description": "Memorial Day observance"
            })
        
        # Labor Day (1st Monday in September)
        labor_day = CorporateLeaveAIService._get_nth_weekday_of_month(year, 9, 0, 1)
        if labor_day:
            floating_holidays.append({
                "date": labor_day,
                "name": "Labor Day",
                "type": "Federal Holiday",
                "is_recurring": True,
                "description": "Labor Day celebration"
            })
        
        # Columbus Day (2nd Monday in October)
        columbus_day = CorporateLeaveAIService._get_nth_weekday_of_month(year, 10, 0, 2)
        if columbus_day:
            floating_holidays.append({
                "date": columbus_day,
                "name": "Columbus Day",
                "type": "Federal Holiday",
                "is_recurring": True,
                "description": "Columbus Day observance"
            })
        
        # Veterans Day (November 11)
        veterans_day = date(year, 11, 11)
        floating_holidays.append({
            "date": veterans_day,
            "name": "Veterans Day",
            "type": "Federal Holiday",
            "is_recurring": True,
            "description": "Veterans Day observance"
        })
        
        # Thanksgiving Day (4th Thursday in November)
        thanksgiving = CorporateLeaveAIService._get_nth_weekday_of_month(year, 11, 3, 4)  # 3 = Thursday
        if thanksgiving:
            floating_holidays.append({
                "date": thanksgiving,
                "name": "Thanksgiving Day",
                "type": "Federal Holiday",
                "is_recurring": True,
                "description": "Thanksgiving Day"
            })
        
        return floating_holidays
    
    @staticmethod
    def _generate_corporate_specific_holidays(year: int) -> List[Dict[str, Any]]:
        """
        Generate corporate-specific holidays and observances.
        
        Args:
            year: Year for which to generate corporate holidays
            
        Returns:
            List of corporate-specific holiday dictionaries
        """
        corporate_holidays = []
        
        # Good Friday (Friday before Easter)
        easter = CorporateLeaveAIService._get_easter_date(year)
        if easter:
            # Calculate Good Friday (2 days before Easter)
            good_friday = easter - timedelta(days=2)
            corporate_holidays.append({
                "date": good_friday,
                "name": "Good Friday",
                "type": "Religious Holiday",
                "is_recurring": True,
                "description": "Good Friday observance"
            })
        
        # Black Friday (Day after Thanksgiving)
        thanksgiving = CorporateLeaveAIService._get_nth_weekday_of_month(year, 11, 3, 4)
        if thanksgiving:
            black_friday = thanksgiving + timedelta(days=1)
            corporate_holidays.append({
                "date": black_friday,
                "name": "Black Friday",
                "type": "Commercial Holiday",
                "is_recurring": True,
                "description": "Day after Thanksgiving"
            })
        
        # Corporate year-end closure (typically last week of December)
        year_end_start = date(year, 12, 26)  # Day after Christmas
        year_end_end = date(year + 1, 1, 1)   # New Year's Day
        
        # Add year-end break if it falls on weekdays
        current_date = year_end_start
        while current_date < year_end_end:
            if current_date.weekday() < 5:  # Monday=0, Sunday=6, so weekday < 5 means Mon-Fri
                corporate_holidays.append({
                    "date": current_date,
                    "name": "Year-end Corporate Closure",
                    "type": "Corporate Holiday",
                    "is_recurring": True,
                    "description": "Corporate office closure for year-end"
                })
            current_date += timedelta(days=1)
        
        return corporate_holidays
    
    @staticmethod
    def _get_nth_weekday_of_month(year: int, month: int, weekday: int, nth: int) -> date:
        """
        Get the nth weekday of a given month.
        
        Args:
            year: Year
            month: Month (1-12)
            weekday: Weekday (0=Monday, 6=Sunday)
            nth: Which occurrence (1st, 2nd, 3rd, 4th, 5th)
            
        Returns:
            Date of the nth weekday in the month
        """
        # Get the first day of the month
        first_day = date(year, month, 1)
        
        # Find the first occurrence of the desired weekday
        days_until_weekday = (weekday - first_day.weekday()) % 7
        first_occurrence = first_day + timedelta(days=days_until_weekday)
        
        # Calculate the nth occurrence
        nth_occurrence = first_occurrence + timedelta(weeks=nth - 1)
        
        # Check if the nth occurrence is still in the same month
        if nth_occurrence.month == month:
            return nth_occurrence
        else:
            return None
    
    @staticmethod
    def _get_last_weekday_of_month(year: int, month: int, weekday: int) -> date:
        """
        Get the last occurrence of a weekday in a given month.
        
        Args:
            year: Year
            month: Month (1-12)
            weekday: Weekday (0=Monday, 6=Sunday)
            
        Returns:
            Date of the last weekday in the month
        """
        # Get the last day of the month
        if month == 12:
            next_month_first = date(year + 1, 1, 1)
        else:
            next_month_first = date(year, month + 1, 1)
        
        last_day = next_month_first - timedelta(days=1)
        
        # Find the last occurrence of the desired weekday
        days_back = (last_day.weekday() - weekday) % 7
        last_occurrence = last_day - timedelta(days=days_back)
        
        return last_occurrence
    
    @staticmethod
    def _get_easter_date(year: int) -> date:
        """
        Calculate Easter date for a given year using the Gregorian calendar algorithm.
        
        Args:
            year: Year
            
        Returns:
            Date of Easter Sunday
        """
        # Anonymous Gregorian algorithm
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        n = (h + l - 7 * m + 114) // 31
        p = (h + l - 7 * m + 114) % 31
        
        return date(year, n, p + 1)
    

    @staticmethod
    def get_regional_holidays(region: str) -> Dict[str, List[str]]:
        """
        Get region-specific holiday information.
        
        Args:
            region: Region/country code
            
        Returns:
            Dictionary mapping regions to lists of holiday types
        """
        regional_holidays = {
            "general": [
                "New Year's Day", "Independence Day", "Christmas Day",
                "Martin Luther King Jr. Day", "Presidents' Day", "Memorial Day",
                "Labor Day", "Columbus Day", "Veterans Day", "Thanksgiving Day"
            ],
            "india": [
                "Republic Day", "Independence Day", "Gandhi Jayanti",
                "Diwali", "Holi", "Dussehra", "Eid al-Fitr", "Eid al-Adha", 
                "Christmas Day", "New Year's Day", "Ganesh Chaturthi", "Navratri"
            ],
            "uk": [
                "New Year's Day", "Good Friday", "Easter Monday",
                "Early May Bank Holiday", "Spring Bank Holiday", "Summer Bank Holiday",
                "Christmas Day", "Boxing Day"
            ]
        }
        
        return regional_holidays.get(region, regional_holidays["general"])
    
    @staticmethod
    def generate_religious_festivals(year: int, region: str = "general") -> List[Dict[str, Any]]:
        """
        Generate religious festivals for the given year and region.
        
        Args:
            year: Year for which to generate festivals
            region: Region for specific festivals
            
        Returns:
            List of religious festival dictionaries
        """
        festivals = []
        
        # Hindu Festivals (using simplified lunar calculations)
        if region in ["india", "general"]:
            festivals.extend(CorporateLeaveAIService._generate_hindu_festivals(year))
        
        # Islamic Festivals (using lunar calendar approximation)
        if region in ["india", "general", "uk"]:
            festivals.extend(CorporateLeaveAIService._generate_islamic_festivals(year))
        
        # Christian Festivals
        if region in ["general", "uk", "india"]:
            festivals.extend(CorporateLeaveAIService._generate_christian_festivals(year))
        
        # Regional Festivals
        if region == "china":
            festivals.extend(CorporateLeaveAIService._generate_chinese_festivals(year))
        
        return festivals
    
    @staticmethod
    def _generate_hindu_festivals(year: int) -> List[Dict[str, Any]]:
        """
        Generate Hindu festivals using lunar calendar approximations.
        
        Args:
            year: Year for which to generate festivals
            
        Returns:
            List of Hindu festival dictionaries
        """
        festivals = []
        
        # Holi - March full moon (approximate)
        holi_dates = {
            2024: date(2024, 3, 25),
            2025: date(2025, 3, 14),
            2026: date(2026, 3, 3),
            2027: date(2027, 2, 20),
            2028: date(2028, 2, 8),
            2029: date(2029, 1, 27),
        }
        
        if year in holi_dates:
            festivals.append({
                "date": holi_dates[year],
                "name": "Holi",
                "type": "Religious Holiday",
                "is_recurring": True,
                "description": "Festival of Colors"
            })
        
        # Diwali - October/November dark moon (approximate)
        diwali_dates = {
            2024: date(2024, 10, 31),
            2025: date(2025, 10, 20),
            2026: date(2026, 10, 9),
            2027: date(2027, 10, 29),
            2028: date(2028, 10, 17),
            2029: date(2029, 10, 6),
        }
        
        if year in diwali_dates:
            festivals.append({
                "date": diwali_dates[year],
                "name": "Diwali",
                "type": "Religious Holiday",
                "is_recurring": True,
                "description": "Festival of Lights"
            })
        
        # Dussehra - September/October (approximate)
        dussehra_dates = {
            2024: date(2024, 10, 15),
            2025: date(2025, 10, 3),
            2026: date(2026, 9, 23),
            2027: date(2027, 10, 12),
            2028: date(2028, 9, 30),
            2029: date(2029, 9, 19),
        }
        
        if year in dussehra_dates:
            festivals.append({
                "date": dussehra_dates[year],
                "name": "Dussehra",
                "type": "Religious Holiday",
                "is_recurring": True,
                "description": "Vijayadasami"
            })
        
        # Ganesh Chaturthi - August/September (approximate)
        ganesh_dates = {
            2024: date(2024, 9, 7),
            2025: date(2025, 8, 27),
            2026: date(2026, 8, 16),
            2027: date(2027, 9, 5),
            2028: date(2028, 8, 24),
            2029: date(2029, 8, 13),
        }
        
        if year in ganesh_dates:
            festivals.append({
                "date": ganesh_dates[year],
                "name": "Ganesh Chaturthi",
                "type": "Religious Holiday",
                "is_recurring": True,
                "description": "Birthday of Lord Ganesha"
            })
        
        return festivals
    
    @staticmethod
    def _generate_islamic_festivals(year: int) -> List[Dict[str, Any]]:
        """
        Generate Islamic festivals using lunar calendar approximations.
        
        Args:
            year: Year for which to generate festivals
            
        Returns:
            List of Islamic festival dictionaries
        """
        festivals = []
        
        # Eid al-Fitr (approximate dates)
        eid_fitr_dates = {
            2024: date(2024, 4, 10),
            2025: date(2025, 3, 31),
            2026: date(2026, 3, 21),
            2027: date(2027, 3, 10),
            2028: date(2028, 2, 27),
            2029: date(2029, 2, 15),
        }
        
        if year in eid_fitr_dates:
            festivals.append({
                "date": eid_fitr_dates[year],
                "name": "Eid al-Fitr",
                "type": "Religious Holiday",
                "is_recurring": True,
                "description": "Festival breaking the fast"
            })
        
        # Eid al-Adha (approximate dates)
        eid_adha_dates = {
            2024: date(2024, 6, 17),
            2025: date(2025, 6, 6),
            2026: date(2026, 5, 27),
            2027: date(2027, 5, 16),
            2028: date(2028, 5, 4),
            2029: date(2029, 4, 24),
        }
        
        if year in eid_adha_dates:
            festivals.append({
                "date": eid_adha_dates[year],
                "name": "Eid al-Adha",
                "type": "Religious Holiday",
                "is_recurring": True,
                "description": "Festival of Sacrifice"
            })
        
        return festivals
    
    @staticmethod
    def _generate_christian_festivals(year: int) -> List[Dict[str, Any]]:
        """
        Generate Christian festivals including Easter-dependent dates.
        
        Args:
            year: Year for which to generate festivals
            
        Returns:
            List of Christian festival dictionaries
        """
        festivals = []
        
        # Easter Sunday
        easter = CorporateLeaveAIService._get_easter_date(year)
        if easter:
            # Good Friday (2 days before Easter)
            good_friday = easter - timedelta(days=2)
            festivals.append({
                "date": good_friday,
                "name": "Good Friday",
                "type": "Religious Holiday",
                "is_recurring": True,
                "description": "Good Friday observance"
            })
            
            # Easter Monday (day after Easter)
            easter_monday = easter + timedelta(days=1)
            festivals.append({
                "date": easter_monday,
                "name": "Easter Monday",
                "type": "Religious Holiday",
                "is_recurring": True,
                "description": "Easter Monday"
            })
        
        return festivals
    
    @staticmethod
    def _generate_chinese_festivals(year: int) -> List[Dict[str, Any]]:
        """
        Generate Chinese festivals and cultural holidays.
        
        Args:
            year: Year for which to generate festivals
            
        Returns:
            List of Chinese festival dictionaries
        """
        festivals = []
        
        # Chinese New Year (approximate)
        chinese_new_year_dates = {
            2024: date(2024, 2, 10),
            2025: date(2025, 1, 29),
            2026: date(2026, 2, 17),
            2027: date(2027, 2, 6),
            2028: date(2028, 1, 26),
            2029: date(2029, 2, 13),
        }
        
        if year in chinese_new_year_dates:
            festivals.append({
                "date": chinese_new_year_dates[year],
                "name": "Chinese New Year",
                "type": "Cultural Holiday",
                "is_recurring": True,
                "description": "Lunar New Year"
            })
        
        return festivals
