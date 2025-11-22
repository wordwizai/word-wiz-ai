# User Statistics Endpoint Implementation Guide

## Overview

This guide provides a step-by-step implementation plan for creating a `/feedback/statistics` endpoint that returns real user statistics for the Dashboard. The implementation follows the **80/20 principle**: focus on getting core functionality working quickly without over-engineering.

### Statistics Provided

- **Total Sessions**: Count of all practice sessions (completed or in-progress)
- **Current Streak**: Number of consecutive days with at least one practice session
- **Longest Streak**: Historical maximum streak achieved
- **Words Read**: Total word count from all feedback entries

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Dashboard.tsx)                                    │
│  - Fetches statistics on mount                              │
│  - Displays in StatCard components                          │
└────────────────────┬────────────────────────────────────────┘
                     │ GET /feedback/statistics
                     │ Authorization: Bearer {token}
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend Router (routers/feedback.py)                       │
│  - @router.get("/statistics")                               │
│  - Authenticates user                                       │
│  - Calls CRUD function                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  CRUD Layer (crud/feedback_entry.py)                        │
│  - get_user_statistics(db, user_id)                         │
│  - Queries sessions, feedback entries                       │
│  - Calculates streaks and word counts                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Database Models                                             │
│  - Session: user_id, created_at, is_completed               │
│  - FeedbackEntry: session_id, sentence, phoneme_analysis    │
└─────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: Create Response Schema

**Goal**: Define the data structure for statistics response

### Step 1.1: Create UserStatistics Schema

**File**: `backend/schemas/feedback_entry.py`

**Action**: Add the following class at the end of the file:

```python
class UserStatistics(BaseModel):
    """User statistics for dashboard display"""
    total_sessions: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    words_read: int = 0

    model_config = {"from_attributes": True}
```

**Explanation**:

- `BaseModel`: Pydantic model for automatic validation and serialization
- Default values of `0` ensure graceful handling of empty data
- `model_config`: Allows creation from SQLAlchemy models if needed

**Quality Checks**:

- [x] Schema compiles without errors
- [x] All fields have appropriate types (int)
- [x] Default values are set

**Status**: ✅ **COMPLETED**

---

## PHASE 2: Implement CRUD Function

**Goal**: Create database queries to calculate all statistics

### Step 2.1: Add Statistics Calculation Function

**File**: `backend/crud/feedback_entry.py`

**Action**: Add these imports at the top:

```python
from datetime import date, timedelta
from sqlalchemy import func, distinct
```

**Action**: Add the following function at the end of the file:

```python
def get_user_statistics(db: Session, user_id: int) -> dict:
    """
    Calculate comprehensive user statistics for dashboard.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        Dictionary with total_sessions, current_streak, longest_streak, words_read
    """
    # 1. Get total sessions (all sessions, not just completed)
    total_sessions = (
        db.query(SessionModel)
        .filter(SessionModel.user_id == user_id)
        .count()
    )

    # 2. Get all session dates for streak calculation
    all_sessions = (
        db.query(SessionModel.created_at)
        .filter(SessionModel.user_id == user_id)
        .order_by(SessionModel.created_at.desc())
        .all()
    )

    # Extract unique dates (convert datetime to date)
    session_dates = sorted(
        set(session.created_at.date() for session in all_sessions),
        reverse=True
    )

    # Calculate streaks
    current_streak, longest_streak = calculate_streaks(session_dates)

    # 3. Calculate total words read from feedback entries
    feedback_entries = get_feedback_entries_by_user(
        db, user_id=user_id, skip=0, limit=10000  # High limit to get all
    )

    words_read = 0
    for entry in feedback_entries:
        if entry.sentence:
            # Simple word count: split by whitespace
            words_read += len(entry.sentence.split())

    return {
        "total_sessions": total_sessions,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "words_read": words_read,
    }


def calculate_streaks(session_dates: list[date]) -> tuple[int, int]:
    """
    Calculate current and longest streaks from a list of session dates.

    Algorithm (80/20 approach):
    - Current streak: Count backwards from today while dates are consecutive
    - Longest streak: Find maximum consecutive sequence in history

    Args:
        session_dates: List of dates (must be sorted descending)

    Returns:
        Tuple of (current_streak, longest_streak)
    """
    if not session_dates:
        return 0, 0

    today = date.today()

    # Calculate current streak
    current_streak = 0
    expected_date = today

    for session_date in session_dates:
        if session_date == expected_date:
            current_streak += 1
            expected_date -= timedelta(days=1)
        elif session_date < expected_date:
            # Gap found, stop counting current streak
            break

    # Calculate longest streak (iterate through all dates)
    longest_streak = 0
    temp_streak = 1

    # Sort ascending for easier consecutive checking
    sorted_dates = sorted(set(session_dates))

    for i in range(len(sorted_dates) - 1):
        days_diff = (sorted_dates[i + 1] - sorted_dates[i]).days

        if days_diff == 1:
            # Consecutive day
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            # Gap found, reset temporary streak
            temp_streak = 1

    # Don't forget to check the final streak
    longest_streak = max(longest_streak, temp_streak, current_streak)

    return current_streak, longest_streak
```

**Explanation**:

1. **Total Sessions**: Simple COUNT query filtered by user_id (counts all sessions, not just completed)
2. **Session Dates**: Extract all session dates for streak calculation (whether completed or not)
3. **Streak Algorithm**:
   - **Current Streak**: Start from today, count backwards while dates are consecutive
   - **Longest Streak**: Find maximum consecutive sequence in entire history
   - Uses date arithmetic to check if days are consecutive
4. **Words Read**:
   - Reuses existing `get_feedback_entries_by_user` function
   - Splits sentences by whitespace and counts words
   - Simple but effective (80/20 approach)

**Edge Cases Handled**:

- No sessions: Returns all zeros
- No sessions today: Current streak = 0
- Multiple sessions same day: Counted as one day (uses `set()`)
- Null/empty sentences: Safely skipped

**Quality Checks**:

- [x] Function compiles without errors
- [x] All imports are present
- [x] Returns dictionary with all required keys
- [x] Handles empty data gracefully

**Status**: ✅ **COMPLETED**

---

## PHASE 3: Create API Endpoint

**Goal**: Expose statistics through REST API

### Step 3.1: Add Statistics Endpoint

**File**: `backend/routers/feedback.py`

**Action**: Add import at the top:

```python
from crud.feedback_entry import get_feedback_entries_by_user, get_user_statistics
from schemas.feedback_entry import FeedbackEntryOut, UserStatistics
```

**Action**: Add the following route at the end of the file:

```python
@router.get("/statistics", response_model=UserStatistics)
def get_user_statistics_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive user statistics for dashboard.

    Returns:
        - total_sessions: Count of all practice sessions (completed or in-progress)
        - current_streak: Consecutive days with sessions (from today backwards)
        - longest_streak: Maximum streak ever achieved
        - words_read: Total words practiced across all feedback entries

    Requires authentication.
    """
    try:
        stats = get_user_statistics(db, user_id=current_user.id)
        return UserStatistics(**stats)
    except Exception as e:
        # Log error in production
        print(f"Error fetching user statistics: {e}")
        # Return zeros instead of failing
        return UserStatistics()
```

**Explanation**:

- **Route**: `GET /feedback/statistics`
- **Authentication**: Required via `get_current_user` dependency
- **Error Handling**: Returns zero values if calculation fails (graceful degradation)
- **Response Model**: Automatically validates and serializes using Pydantic

**Quality Checks**:

- [x] Endpoint appears in FastAPI docs (`/docs`)
- [x] Requires authentication (401 without token)
- [x] Returns correct JSON structure
- [x] Handles errors gracefully

**Status**: ✅ **COMPLETED** - Ready to test at http://localhost:8000/docs

---

## PHASE 4: Frontend Integration

**Goal**: Fetch and display real statistics in Dashboard

### Step 4.1: Add API Function

**File**: `frontend/src/api.ts`

**Action**: Find the file and add this function (or update existing if api structure differs):

```typescript
export interface UserStatistics {
  total_sessions: number;
  current_streak: number;
  longest_streak: number;
  words_read: number;
}

export const getUserStatistics = async (
  token: string
): Promise<UserStatistics> => {
  const response = await fetch(`${API_BASE_URL}/feedback/statistics`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch user statistics");
  }

  return response.json();
};
```

**Explanation**:

- TypeScript interface matches backend schema
- Uses existing auth token from context
- Throws error for failed requests (handled by component)

### Step 4.2: Update Dashboard Component

**File**: `frontend/src/pages/Dashboard.tsx`

**Action**: Add import at the top:

```typescript
import { getUserStatistics, type UserStatistics } from "@/api";
```

**Action**: Add state management after existing useState declarations:

```typescript
const [statistics, setStatistics] = useState<UserStatistics | null>(null);
const [statsLoading, setStatsLoading] = useState(true);
const [statsError, setStatsError] = useState<string | null>(null);
```

**Action**: Add useEffect to fetch statistics:

```typescript
// Fetch user statistics
useEffect(() => {
  const fetchStatistics = async () => {
    if (!token) return;

    try {
      setStatsLoading(true);
      setStatsError(null);
      const stats = await getUserStatistics(token);
      setStatistics(stats);
    } catch (error) {
      console.error("Error fetching statistics:", error);
      setStatsError("Failed to load statistics");
    } finally {
      setStatsLoading(false);
    }
  };

  fetchStatistics();
}, [token]);
```

**Action**: Update StatCard components to use real data:

Replace these lines:

```typescript
<StatCard
  icon={Target}
  label="Sessions"
  value={pastSessions.length.toString()}
  color="bg-pastel-blue"
  iconColor="text-blue-600"
/>
<StatCard
  icon={Flame}
  label="Streak"
  value="5 days"
  color="bg-pastel-yellow"
  iconColor="text-orange-600"
/>
<StatCard
  icon={BookOpen}
  label="Words Read"
  value="342"
  color="bg-pastel-mint"
  iconColor="text-green-600"
/>
<StatCard
  icon={Palette}
  label="Activities"
  value="8"
  color="bg-pastel-coral"
  iconColor="text-pink-600"
/>
```

With:

```typescript
<StatCard
  icon={Target}
  label="Sessions"
  value={statsLoading ? "..." : (statistics?.total_sessions?.toString() || "0")}
  color="bg-pastel-blue"
  iconColor="text-blue-600"
/>
<StatCard
  icon={Flame}
  label="Current Streak"
  value={statsLoading ? "..." : `${statistics?.current_streak || 0} days`}
  color="bg-pastel-yellow"
  iconColor="text-orange-600"
/>
<StatCard
  icon={BookOpen}
  label="Words Read"
  value={statsLoading ? "..." : (statistics?.words_read?.toString() || "0")}
  color="bg-pastel-mint"
  iconColor="text-green-600"
/>
<StatCard
  icon={Target}
  label="Longest Streak"
  value={statsLoading ? "..." : `${statistics?.longest_streak || 0} days`}
  color="bg-pastel-coral"
  iconColor="text-pink-600"
/>
```

**Explanation**:

- Shows "..." while loading
- Falls back to "0" if data unavailable
- Formats streak values with "days" suffix
- Handles null/undefined gracefully with optional chaining

**Alternative**: If you want to keep "Activities" instead of "Longest Streak", you can query the activities count separately or keep it as a future enhancement.

**Quality Checks**:

- [ ] Dashboard shows loading state briefly
- [ ] Real statistics appear after load
- [ ] No console errors
- [ ] Stats update after completing a session (refresh)

---

## PHASE 5: Testing & Validation

**Goal**: Ensure accuracy and reliability

### Step 5.1: Backend Testing

**Manual Tests**:

1. **Test with no data**:

   - Create new test user with no sessions
   - Call `/feedback/statistics`
   - Expected: All values = 0

2. **Test with single session**:

   - Create one completed session today
   - Expected: total_sessions=1, current_streak=1, longest_streak=1

3. **Test consecutive days**:

   - Create sessions for last 3 consecutive days
   - Expected: current_streak=3, longest_streak=3

4. **Test broken streak**:

   - Create sessions for 5 days ago, 4 days ago, 3 days ago, then today
   - Expected: current_streak=1, longest_streak=3

5. **Test words count**:
   - Create feedback entry with sentence "Hello world test"
   - Expected: words_read includes those 3 words

**Test Using FastAPI Docs**:

1. Go to `http://localhost:8000/docs`
2. Authorize using your JWT token
3. Execute `GET /feedback/statistics`
4. Verify response structure and values

### Step 5.2: Frontend Testing

**Visual Tests**:

1. **Login and view dashboard**:

   - Stats should load within 1-2 seconds
   - No flickering or errors

2. **Complete a new session**:

   - Navigate to practice, complete activity
   - Return to dashboard (or refresh)
   - Stats should update (especially total_sessions and current_streak)

3. **Test error handling**:
   - Temporarily break API URL to simulate failure
   - Dashboard should show "0" values or error message
   - No crashes or blank screen

### Step 5.3: Performance Testing

**Benchmarks** (80/20 rule - good enough targets):

- [ ] API response time < 500ms for typical user (10-100 sessions)
- [ ] API response time < 2s for power user (1000+ sessions)
- [ ] Dashboard loads without blocking UI

**If performance is slow**:

- Add database index on `sessions.user_id` and `sessions.created_at`
- Consider caching statistics (update on session completion)
- Limit feedback entries query (pagination)

---

## PHASE 6: Optional Enhancements

**Only implement if time permits and core functionality is solid**

### Enhancement 6.1: Add Caching

If statistics calculation is slow (>1 second), add simple caching:

**File**: `backend/models/user.py`

Add fields:

```python
cached_statistics = Column(JSON, default={})
statistics_updated_at = Column(DateTime(timezone=True), nullable=True)
```

Update statistics on session completion:

```python
# In routers/session.py - after marking session complete
from crud.feedback_entry import get_user_statistics
stats = get_user_statistics(db, current_user.id)
current_user.cached_statistics = stats
current_user.statistics_updated_at = func.now()
db.commit()
```

### Enhancement 6.2: Real-time Updates

Update statistics immediately after session completion without page refresh:

**Frontend**: Call `fetchStatistics()` after deactivating session

```typescript
// In practice completion flow
await deactivateSession(sessionId);
await fetchStatistics(); // Refresh stats
```

### Enhancement 6.3: Historical Tracking

Add a `daily_statistics` table to track progress over time:

- Store daily snapshots
- Enable charts and progress graphs
- Analyze trends

**Note**: This is beyond 80/20 scope - implement only if analytics features are required.

---

## Troubleshooting Guide

### Issue: "Module has no attribute 'get_user_statistics'"

**Cause**: Import not updated or function name mismatch

**Fix**:

1. Check `crud/feedback_entry.py` has the function
2. Verify import in `routers/feedback.py`
3. Restart FastAPI server

### Issue: "Streaks are incorrect"

**Cause**: Timezone mismatch or date calculation bug

**Fix**:

1. Ensure all dates use `.date()` conversion
2. Check `created_at` timezone is consistent
3. Add debug prints to `calculate_streaks()` to trace logic

### Issue: "Words count seems low"

**Cause**: Not all feedback entries have sentences

**Fix**:

1. Verify feedback entries exist: `SELECT COUNT(*) FROM feedback_entries`
2. Check for null/empty sentences
3. Ensure sessions are marked as completed

### Issue: "API returns 500 error"

**Cause**: Database query failure or missing data

**Fix**:

1. Check backend logs for exception details
2. Verify database models are correct
3. Ensure foreign keys are properly set up
4. Test with try/catch and return safe defaults

### Issue: "Frontend shows 0 for all stats but backend returns data"

**Cause**: Type mismatch or state not updating

**Fix**:

1. Check browser console for errors
2. Verify API response structure matches TypeScript interface
3. Ensure `setStatistics()` is called after successful fetch
4. Check if `statistics` state is null vs. populated

---

## Success Criteria Checklist

### Backend

- [ ] UserStatistics schema created and importable
- [ ] `get_user_statistics()` function implemented in CRUD layer
- [ ] Streak calculation algorithm working correctly
- [ ] Words count calculation implemented
- [ ] `/feedback/statistics` endpoint created
- [ ] Endpoint requires authentication
- [ ] Returns correct JSON structure
- [ ] Handles errors gracefully (returns zeros)

### Frontend

- [ ] `getUserStatistics()` API function created
- [ ] Dashboard fetches statistics on mount
- [ ] Loading state displays during fetch
- [ ] Real statistics display in StatCards
- [ ] No console errors
- [ ] Graceful error handling (shows 0 on failure)

### Testing

- [ ] Tested with user with no sessions (all zeros)
- [ ] Tested with active user (real data)
- [ ] Streak calculation verified manually
- [ ] Words count matches expectations
- [ ] Performance acceptable (<500ms typical)

### Documentation

- [ ] Code comments explain complex logic
- [ ] API endpoint documented in FastAPI auto-docs
- [ ] This implementation guide completed

---

## Estimated Timeline

Following 80/20 principle (core functionality only):

| Phase     | Tasks                   | Time Estimate  |
| --------- | ----------------------- | -------------- |
| Phase 1   | Create schema           | 10 minutes     |
| Phase 2   | Implement CRUD function | 45 minutes     |
| Phase 3   | Create API endpoint     | 20 minutes     |
| Phase 4   | Frontend integration    | 40 minutes     |
| Phase 5   | Testing & validation    | 30 minutes     |
| **Total** | **Core implementation** | **~2.5 hours** |

Optional enhancements (Phase 6): +1-2 hours each

---

## Next Steps After Implementation

1. **Monitor Usage**: Check API logs for errors or slow queries
2. **Gather Feedback**: Ask users if statistics are accurate and useful
3. **Iterate**: Add more statistics if needed (e.g., favorite activity, practice time)
4. **Optimize**: Add indexes or caching if performance degrades with scale
5. **Visualize**: Consider adding charts/graphs for historical trends (Phase 6+)

---

## Related Files Reference

**Backend Files**:

- `backend/routers/feedback.py` - API endpoint
- `backend/crud/feedback_entry.py` - Database queries
- `backend/schemas/feedback_entry.py` - Response schema
- `backend/models/session.py` - Session model
- `backend/models/feedback_entry.py` - Feedback model

**Frontend Files**:

- `frontend/src/api.ts` - API client functions
- `frontend/src/pages/Dashboard.tsx` - Statistics display
- `frontend/src/components/ui/card.tsx` - StatCard component

**Database Tables**:

- `sessions` - User practice sessions
- `feedback_entries` - Phoneme analysis and sentences
- `users` - User information

---

## Additional Notes

### Why Feedback Router?

The statistics endpoint is placed in the feedback router because:

1. **Data Source**: All statistics derive primarily from `feedback_entries` table
2. **Existing Patterns**: Other user-specific feedback queries already exist here
3. **Cohesion**: Keeps all user feedback/progress data in one logical location
4. **Simplicity**: Avoids creating a new router for a single endpoint

### Why 80/20 Approach?

This implementation focuses on:

- ✅ **Getting it working quickly**: No premature optimization
- ✅ **Real data**: Replaces hardcoded values with actual statistics
- ✅ **Simple algorithms**: Good enough accuracy without complex logic
- ✅ **Graceful degradation**: Returns zeros instead of crashing

Explicitly NOT included (can add later if needed):

- ❌ Complex caching layers
- ❌ Historical tracking tables
- ❌ Advanced timezone handling
- ❌ Detailed analytics and reports
- ❌ Real-time WebSocket updates

**Result**: Fully functional statistics in ~2-3 hours instead of days of over-engineering.

---

**Document Version**: 1.0  
**Last Updated**: November 22, 2025  
**Author**: Implementation Guide Generator  
**Status**: Ready for Implementation
