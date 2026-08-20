# API Contract Alignment with BE-1

## ✅ Changes Made

All changes align the **frontend API service layer** with BE-1 backend contract requirements.

**Status:** ✅ Complete - Ready for BE-1 integration testing

---

## 🔄 Changed Files

### 1. `src/services/api.js`
- Updated API base URL
- Modified analysis request payload format
- Added BE-1 contract documentation

### 2. `src/pages/Analysis.jsx`
- Updated payload to send NAMES instead of IDs
- Added inline documentation

---

## 📋 Detailed Changes

### Change 1: API Base URL

**Before:**
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
```

**After:**
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
```

**Impact:** All API requests now use `/api/v1` prefix

---

### Change 2: Analysis Endpoint Path

**Before:**
```javascript
const response = await api.post('/analysis', payload);
```

**After:**
```javascript
const response = await api.post('/analysis/', payload);
```

**Full Path:** `POST http://localhost:8000/api/v1/analysis/`

**Impact:** Endpoint now includes trailing slash as required by BE-1

---

### Change 3: Analysis Request Payload

**Before (sending IDs):**
```javascript
const payload = {
  state: state.code,              // "CA"
  counties: counties.map(c => c.id),     // [1, 2, 3]
  specialties: specialties.map(s => s.id) // [1, 2]
};
```

**After (sending NAMES):**
```javascript
const payload = {
  state: state.code,                      // "CA"
  counties: counties.map(c => c.name),    // ["Los Angeles", "San Diego"]
  specialties: specialties.map(s => s.name) // ["Cardiology", "Psychiatry"]
};
```

**Example Payload Sent to BE-1:**
```json
{
  "state": "CA",
  "counties": ["Los Angeles", "San Diego"],
  "specialties": ["Cardiology", "Psychiatry"]
}
```

**Impact:** Backend receives human-readable names instead of numeric IDs

---

### Change 4: Added Console Logging (Mock Mode)

**Added to `submitAnalysis`:**
```javascript
console.log('[API] Analysis payload prepared for BE-1:', JSON.stringify(payload, null, 2));
```

**Purpose:** When `USE_MOCK_DATA = true`, logs the exact payload that would be sent to BE-1

**Example Console Output:**
```
[API] Analysis payload prepared for BE-1: {
  "state": "CA",
  "counties": [
    "Los Angeles",
    "San Diego"
  ],
  "specialties": [
    "Cardiology",
    "Psychiatry"
  ]
}
```

---

### Change 5: Updated Documentation Comments

**Added to `api.js`:**
```javascript
/**
 * API CONTRACT ALIGNMENT WITH BE-1
 * 
 * Base URL: http://localhost:8000/api/v1
 * 
 * Analysis Endpoint: POST /api/v1/analysis/
 * 
 * Request Payload Format:
 * {
 *   "state": "CA",                        // State code as string
 *   "counties": ["Los Angeles", "..."],    // County NAMES (not IDs)
 *   "specialties": ["Cardiology", "..."]   // Specialty NAMES (not IDs)
 * }
 * 
 * Frontend keeps IDs internally for UI selection, but sends NAMES to backend.
 */
```

---

## 🎯 What Was NOT Changed

### ✅ UI Remains Unchanged
- All React components work exactly the same
- User experience is identical
- Selection screens still use IDs internally
- Mock data structure unchanged

### ✅ Data Model Kept
- Specialty IDs (1-12) retained for UI selection
- County IDs retained for UI selection
- Category field kept (frontend-only, not sent to backend)

### ✅ Mock Data Still Works
- `USE_MOCK_DATA = true` (unchanged)
- Mock responses unchanged
- Frontend still functional without backend

### ✅ No Backend Changes
- Did NOT create `/areas`, `/providers`, `/recommendations` endpoints
- Did NOT modify backend code
- Did NOT assume final response structure from BE-1

---

## 🧪 Testing the Changes

### Test 1: Verify Payload Format (Mock Mode)

**Steps:**
1. Open http://localhost:3000
2. Open Browser DevTools → Console tab
3. Run complete flow:
   - Dashboard → Select Area (CA)
   - Select counties: Los Angeles, San Diego
   - Select specialties: Cardiology, Psychiatry
   - Click "Start Analysis"
4. Wait for analysis to complete
5. **Check Console** for log output

**Expected Console Output:**
```
[API] Analysis payload prepared for BE-1: {
  "state": "CA",
  "counties": [
    "Los Angeles",
    "San Diego"
  ],
  "specialties": [
    "Cardiology",
    "Psychiatry"
  ]
}
```

**✅ Success:** Names are being sent (not IDs)

---

### Test 2: Verify Application Still Works

**Steps:**
1. Complete user flow: Dashboard → Select Area → Select Specialty → Analysis → Results
2. Verify Results page displays correctly
3. Verify Recommendations page displays correctly
4. Check for console errors

**Expected Behavior:**
- ✅ No errors in console
- ✅ Results page shows Network Adequacy Score (67)
- ✅ Map displays with 5 gap areas
- ✅ Table view works
- ✅ Recommendations show 5 priority items

---

### Test 3: Verify API Base URL

**Steps:**
1. Open DevTools → Network tab
2. If backend were running, requests would go to:
   - `http://localhost:8000/api/v1/analysis/`
   - NOT `http://localhost:8000/api/analysis`

**With Mock Data:** No actual network requests made, but service is configured correctly

---

## 📊 API Contract Summary

### Endpoint Details

| Aspect | Value |
|--------|-------|
| **Base URL** | `http://localhost:8000/api/v1` |
| **Analysis Endpoint** | `POST /analysis/` |
| **Full Path** | `POST http://localhost:8000/api/v1/analysis/` |
| **Content-Type** | `application/json` |

### Request Format

```typescript
interface AnalysisRequest {
  state: string;           // State code (e.g., "CA", "TX")
  counties: string[];      // County names (e.g., ["Los Angeles"])
  specialties: string[];   // Specialty names (e.g., ["Cardiology"])
}
```

### Example Request

```http
POST http://localhost:8000/api/v1/analysis/
Content-Type: application/json

{
  "state": "CA",
  "counties": ["Los Angeles", "San Diego", "Orange"],
  "specialties": ["Cardiology", "Psychiatry"]
}
```

---

## 🔧 Switching to Real Backend

### Step 1: Enable Backend Mode

**In `src/services/api.js`:**
```javascript
// Change this line:
const USE_MOCK_DATA = false; // Set to false when backend is ready
```

### Step 2: Ensure Backend is Running

```bash
# BE-1 backend should be running on:
http://localhost:8000

# Test endpoint availability:
curl http://localhost:8000/api/v1/
```

### Step 3: Test Integration

1. Run frontend: `npm start` (already running on port 3000)
2. Complete analysis flow
3. Check Network tab for actual API requests
4. Verify backend receives correct payload format

---

## 🚨 Important Notes

### 1. Frontend-Only Changes
- **Only** frontend API service layer was modified
- **No** backend endpoints were created
- **No** assumptions about final BE-1 response structure

### 2. Specialty Names Match BE-1
The 12 specialty names are already aligned with BE-1:
1. Cardiology
2. Pediatrics
3. Orthopedics
4. Dermatology
5. Family Medicine
6. Psychiatry
7. Neurology
8. Oncology
9. Internal Medicine
10. Emergency Medicine
11. Obstetrics & Gynecology
12. Endocrinology

### 3. Category Field (Frontend-Only)
- Category (e.g., "Specialty Care", "Primary Care") is NOT sent to backend
- Only specialty NAME is sent

### 4. Geographic Granularity
- Frontend sends County NAMES
- Backend (BE-1) must aggregate ZIP-level data → County level
- This was already documented and remains a backend concern

### 5. Response Structure
- Mock response structure remains unchanged
- When BE-1 provides final response contract, we can adapt the response handling
- UI is decoupled from response structure

---

## 📁 File Changes Summary

### Modified Files (2)

**1. `src/services/api.js`** (~375 lines)
- Lines changed: ~30
- Base URL updated
- Endpoint path updated
- Console logging added
- Documentation updated

**2. `src/pages/Analysis.jsx`** (~140 lines)
- Lines changed: ~10
- Payload mapping changed (IDs → NAMES)
- Inline comments added

### Total Impact
- **2 files modified**
- **~40 lines changed**
- **0 functional changes** (UI works exactly the same)
- **100% backward compatible** with mock data

---

## ✅ Checklist

### API Contract Alignment
- [x] Base URL changed to `/api/v1`
- [x] Endpoint path changed to `/analysis/` (with trailing slash)
- [x] Payload sends county NAMES (not IDs)
- [x] Payload sends specialty NAMES (not IDs)
- [x] State code sent as string
- [x] Category field NOT sent to backend
- [x] Console logging added for testing
- [x] Documentation updated

### Testing
- [x] Application compiles without errors
- [x] Mock data still works
- [x] UI unchanged
- [x] Payload format verified in console

### Documentation
- [x] API contract documented
- [x] Changes documented
- [x] Testing instructions provided
- [x] Backend integration steps provided

---

## 🔄 Next Steps

### For Frontend Team (FE-1)
1. ✅ Test payload format in console
2. ✅ Verify UI still works with mock data
3. ⏳ Wait for BE-1 final response contract
4. ⏳ Adapt response handling when BE-1 is ready

### For Backend Team (BE-1)
1. ⏳ Implement `/api/v1/analysis/` endpoint
2. ⏳ Accept payload: `{ state, counties[], specialties[] }`
3. ⏳ Map County names → ZIP codes internally
4. ⏳ Return analysis results (structure TBD)
5. ⏳ Coordinate on final response format

### For Testing
1. ⏳ Integration testing with real BE-1 endpoint
2. ⏳ Verify County → ZIP mapping works correctly
3. ⏳ End-to-end testing

---

## 📞 Questions for BE-1

1. **Response Format:** What is the final structure of analysis results?
2. **Error Handling:** What error codes/messages will BE-1 return?
3. **Validation:** Should frontend validate county/specialty names before sending?
4. **Geographic Mapping:** Confirmed that BE-1 will handle County → ZIP aggregation?
5. **Other Endpoints:** When will `/areas`, `/counties`, `/specialties`, `/recommendations` be available?

---

**Status:** ✅ Frontend API contract aligned with BE-1 requirements  
**Mock Data:** ✅ Still enabled and working  
**Ready For:** ⏳ BE-1 integration testing  
**Date:** August 18, 2026
