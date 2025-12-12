# Leave Management API Fix Plan

## Issues Identified:
1. **Balance API**: May have edge cases where default balance creation fails for new employees
2. **History API**: Should handle empty tables gracefully but may have query issues
3. **Default Leave Assignment**: Need to ensure 12 leaves are automatically assigned to all existing employees and new employees

## Plan:

### Step 1: Fix Balance API for Empty Tables
- Enhance the balance endpoint to better handle edge cases
- Ensure proper database transaction handling
- Add better error handling for new employees

### Step 2: Fix History API for Empty Tables  
- Ensure history endpoint returns proper empty responses
- Optimize query for better performance
- Add proper error handling

### Step 3: Implement Automatic Default Leave Assignment
- Create a migration/service to assign 12 days to all existing employees who don't have leave balances
- Enhance the employee creation service to be more robust
- Add validation to ensure no duplicate balances

### Step 4: Test and Validate
- Test the APIs with empty tables
- Test with new employees
- Test with existing employees without balances

## Files to Modify:
- `app/routers/leaves.py` - Fix balance and history endpoints
- `app/services/employee.py` - Enhance employee creation
- Create new migration script for existing employees

## Expected Outcome:
- Balance API works correctly for all employees (new and existing)
- History API returns proper responses for empty and populated tables
- All employees have 12 days leave by default
