# Manual Test Instructions for Extended Login Functionality

## Objective
Verify that the extended login functionality and 'Remember Me' option work as expected and maintain security.

---

## Test Cases

### 1. Standard Login (Without Remember Me)
- **Steps:**
  1. Navigate to the login page.
  2. Enter valid credentials (email and password).
  3. Ensure the 'Remember Me' checkbox is **not selected**.
  4. Submit the login form.
- **Expected Result:**
  - Access token is issued with a default expiration of 30 minutes.
  - After 30 minutes, the token becomes invalid and the user is logged out.

---

### 2. Login with 'Remember Me'
- **Steps:**
  1. Navigate to the login page.
  2. Enter valid credentials (email and password).
  3. Select the 'Remember Me' checkbox.
  4. Submit the login form.
- **Expected Result:**
  - Access token is issued with an extended expiration of 30 days.
  - The token remains valid for 30 days unless manually invalidated.

---

### 3. Security Check for Extended Token
- **Steps:**
  1. Perform the 'Login with Remember Me' test case.
  2. Inspect the token payload to confirm the expiration date is set correctly.
- **Expected Result:**
  - The token expiration (`exp`) matches the extended duration (30 days).

---

### 4. Standard Token Behavior
- **Steps:**
  1. Perform the 'Standard Login' test case.
  2. Inspect the token payload to confirm the expiration date is set correctly.
- **Expected Result:**
  - The token expiration (`exp`) matches the standard duration (30 minutes).

---

### 5. Unauthorized Access After Expiration
- **Steps:**
  1. Perform the 'Standard Login' or 'Login with Remember Me' test case.
  2. Wait for the token to expire.
  3. Attempt to access a protected route using the expired token.
- **Expected Result:**
  - The request is denied with an HTTP 401 Unauthorized error.

---

## Notes
- Use tools like Postman or browser developer tools to inspect tokens and simulate API requests.
- Ensure that no sensitive data is leaked during the login process.

---

## Conclusion
Perform these test cases to validate the extended login functionality and ensure it meets security and usability standards.

