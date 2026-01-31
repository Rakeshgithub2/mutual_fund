# Reminder System - Complete Guide

## ✅ Implementation Complete

The reminder system is now fully functional with all requested features:

### 🎯 Features Implemented

1. **Manual Time Entry**

   - User can type time manually in HH:MM format (e.g., 09:30)
   - AM/PM dropdown for 12-hour format
   - Auto-formatting of time input
   - Validation to ensure correct format

2. **Enhanced Reminder Cards**

   - Beautiful card design similar to goal cards
   - Grid layout (2 columns on desktop)
   - Clear display of all reminder details
   - Status badges (PENDING, SENT, COMPLETED)
   - Type and frequency badges
   - Visual icons for date, time, and notifications

3. **CRUD Operations**

   - ✅ **Create**: Create new reminder with all details
   - ✅ **Read**: View all reminders in beautiful cards
   - ✅ **Update**: Mark reminder as completed
   - ✅ **Delete**: Delete reminder with confirmation
   - Real-time database updates
   - Success/error toast notifications

4. **Email Notifications**
   - Sends reminder email at scheduled date/time
   - Confirmation email when reminder is created
   - Cron job runs every 5 minutes
   - Detailed logging for debugging

## 🧪 How to Test

### Step 1: Create a Test Reminder

1. Go to http://localhost:5001/reminders
2. Click "New Reminder" button
3. Fill in the form:
   - **Type**: Select "Custom" or any type
   - **Frequency**: Select "One Time"
   - **Title**: "Test Reminder"
   - **Description**: "Testing email delivery"
   - **Date**: Select today's date
   - **Time**: Enter a time **2-3 minutes from now** (e.g., if it's 11:30 PM now, enter 11:33)
   - **AM/PM**: Select appropriate period
   - ✅ Ensure "Send email notification" is checked
4. Click "Create Reminder"

### Step 2: Check Confirmation Email

- Check your registered email inbox
- You should receive a confirmation email immediately
- Subject: "Reminder Created: [Your Title]"

### Step 3: Monitor Backend Logs

Watch the backend terminal for reminder job execution:

```
🚀 Starting reminder job...
⏰ Time: 2026-01-06 23:35:00
🔍 Checking for reminders. Current time: 2026-01-06T18:05:00.233Z
🔍 Current time (IST): 6/1/2026, 11:35:00 pm
📋 Found 1 pending reminders
📝 Pending reminders:
  1. Test Reminder - Scheduled: 2026-01-06T18:03:00.000Z
     User: your-email@example.com
     Notify via email: true
📧 Sending reminder: "Test Reminder" to your-email@example.com
✅ Reminder processed and marked as SENT: Test Reminder
```

### Step 4: Check Reminder Email

- Wait for the scheduled time (reminder job runs every 5 minutes)
- Check your email inbox
- You should receive the reminder email
- Subject: "Reminder: [Your Title]"

### Step 5: Verify Status Update

- Refresh the reminders page
- The reminder status should change from "PENDING" to "SENT"
- You can click "Complete" to mark it as completed
- You can click "Delete" to remove it

## 🔍 Testing Script

Run the test script to check reminder timing:

```powershell
cd 'c:\MF root folder\mutual-funds-backend'
node test-reminder-timing.js
```

This will show:

- Current time in UTC, IST, and local timezone
- All pending reminders with scheduled times
- Time until next reminder
- Recently sent reminders
- Cron job schedule

## 📊 System Details

### Frontend (Port 5001)

- **Location**: `c:\MF root folder\mutual fund\app\reminders\page.tsx`
- **Features**:
  - Manual time input with validation
  - AM/PM selector
  - Beautiful card-based UI
  - Real-time CRUD operations
  - Toast notifications
  - Responsive design

### Backend (Port 3002)

- **Cron Job**: Runs every 5 minutes (`*/5 * * * *`)
- **File**: `c:\MF root folder\mutual-funds-backend\src\jobs\reminder.job.js`
- **Email Service**: Uses Resend API
- **Database**: MongoDB with real-time updates

### Time Handling

- User enters time in 12-hour format (e.g., 09:30 AM)
- System converts to 24-hour format for storage
- Stores in UTC timezone
- Job compares with server time every 5 minutes
- Sends email when scheduled time is reached or passed

## 🐛 Troubleshooting

### Email Not Received

1. **Check Backend Logs**

   - Look for "📧 Attempting to send reminder email"
   - Check for any error messages

2. **Verify Email Service**

   - Ensure RESEND_API_KEY is set in `.env`
   - Check email address is verified in Resend dashboard

3. **Check Timing**

   - Run `node test-reminder-timing.js` to verify scheduled time
   - Reminder must be scheduled in the future
   - Job runs every 5 minutes, so there may be up to 5-minute delay

4. **Check Spam Folder**
   - Reminder emails might be in spam/junk folder

### Reminder Not Showing

1. **Check Login Status**

   - User must be logged in
   - Token must be valid

2. **Refresh Page**

   - Click refresh or reload the page
   - Check browser console for errors

3. **Check Database**
   - Run test script to see all reminders
   - Verify reminder was saved correctly

## 📝 Example Use Cases

### Morning SIP Reminder

- **Title**: "Monthly SIP Payment"
- **Type**: SIP
- **Date**: 1st of each month
- **Time**: 09:00 AM
- **Frequency**: Monthly

### Portfolio Review

- **Title**: "Quarterly Portfolio Review"
- **Type**: Portfolio Rebalance
- **Date**: Start of quarter
- **Time**: 10:00 AM
- **Frequency**: Quarterly

### Document Update

- **Title**: "Update KYC Documents"
- **Type**: Document Update
- **Date**: Before expiry
- **Time**: 02:00 PM
- **Frequency**: Yearly

## ✅ Verification Checklist

- [x] User can manually enter time in HH:MM format
- [x] AM/PM dropdown works correctly
- [x] Time is validated and auto-formatted
- [x] Reminder saves to database with correct date/time
- [x] Confirmation email sent on creation
- [x] Reminder email sent at scheduled time
- [x] Reminders displayed in beautiful cards (2-column grid)
- [x] All CRUD operations work (Create, Read, Update, Delete)
- [x] Status updates in real-time (PENDING → SENT → COMPLETED)
- [x] Visual feedback with icons and badges
- [x] Proper error handling and validation
- [x] Detailed logging for debugging
- [x] Cron job runs every 5 minutes
- [x] Timezone handling (UTC storage, local display)

## 🎉 Success Indicators

1. **Confirmation Email Received**: After creating reminder
2. **Backend Logs Show Reminder**: "Found X pending reminders"
3. **Reminder Email Received**: At scheduled time
4. **Status Changes**: PENDING → SENT in UI
5. **CRUD Works**: Can complete and delete reminders

## 📞 Support

If you encounter any issues:

1. Check backend terminal logs
2. Run `node test-reminder-timing.js`
3. Verify `.env` file has RESEND_API_KEY
4. Check MongoDB connection
5. Ensure both servers are running (ports 3002 and 5001)

---

**Last Updated**: January 6, 2026
**Status**: ✅ Fully Functional
