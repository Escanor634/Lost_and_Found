# Campus Lost & Found - Project Status

## Stage Tracking

| Stage | Name | Status | Acceptance Criteria Met |
| :--- | :--- | :--- | :--- |
| **Stage 1** | **Project Setup and Architecture** | **Completed** | Yes |
| **Stage 2** | **Database Design and Models** | **Completed** | Yes |
| **Stage 3** | **User Authentication & Roles** | **Completed** | Yes |
| **Stage 4** | **Frontend UI and Dashboard** | **Completed** | Yes |
| **Stage 5** | **Lost & Found Item Management** | **Completed** | Yes |
| Stage 6 | Search, Filter & Matching | Pending | - |
| **Stage 7** | **Claims & Verification Workflow** | **Completed** | Yes |
| Stage 8 | Notifications & Activity Alerts | Pending | - |
| Stage 9 | Admin Panel & Moderation | Pending | - |
| Stage 10 | Polish, Security & Deployment Prep | Pending | - |

---

## Stage 1 Verification Summary

- [x] Application factory pattern (`create_app`) and blueprint architecture implemented.
- [x] Modular blueprint packages configured (`auth`, `items`, `claims`, `notifications`, `admin`).
- [x] Configuration separated into environment-aware classes in `config.py`.
- [x] SQLite database support configured via Flask-SQLAlchemy with `flask init-db` CLI command.
- [x] Bootstrap 5 responsive layout with navbar, project branding, and placeholder sections for reporting lost/found items.
- [x] GET `/health` endpoint returning JSON HTTP 200.
- [x] Pytest suite configured with comprehensive tests (`tests/test_app.py`) - 8 tests passing.
- [x] README with complete setup, virtual environment, installation, database initialization, execution, and testing instructions.

---

## Stage 2 Verification Summary

- [x] **User Model** (`app/models/user.py`):
  - Fields: `id`, `name`, `email` (unique, indexed), `password_hash`, `role` (student/admin), `status` (active/suspended, with `account_status` alias), `created_at`.
  - Database check constraints and validation hooks for role, status, and email.
- [x] **Item Model** (`app/models/item.py`):
  - Fields: `id`, `user_id` (FK -> users.id, cascade), `title`, `description`, `category` (indexed), `item_type` (lost/found), `color` (optional), `location`, `incident_date` (with date/datetime/ISO-string parsing), `image_path` (optional), `status` (open, claim_pending, recovered, closed), `created_at`, `updated_at`.
  - Check constraints for item_type and status.
- [x] **Claim Model** (`app/models/claim.py`):
  - Fields: `id`, `item_id` (FK -> items.id, cascade), `claimant_id` (FK -> users.id, cascade), `proof_description`, `status` (pending, approved, rejected, withdrawn), `reviewer_id` (FK -> users.id, nullable), `created_at`, `reviewed_at`.
  - Partial unique index on `(item_id, claimant_id)` preventing duplicate active claims (`status IN ('pending', 'approved')`).
  - Partial unique index on `(item_id)` ensuring only one approved claim per item.
  - Review lifecycle helpers (`approve`, `reject`, `withdraw`).
- [x] **Notification Model** (`app/models/notification.py`):
  - Fields: `id`, `user_id` (FK -> users.id, cascade), `message`, `notification_type`, `item_id` (FK -> items.id, nullable, with `related_item_id` alias), `claim_id` (FK -> claims.id, nullable, with `related_claim_id` alias), `is_read`, `created_at`.
  - Helper `mark_as_read`.
- [x] **Database & Migrations**:
  - SQLite foreign key constraints enabled via SQLite `PRAGMA foreign_keys=ON` connection listener.
  - Flask-Migrate integration configured; migration repository created and initial migration applied without database destruction.
- [x] **Test Suite**:
  - All 8 Stage 1 tests continue passing.
  - 29 unit and constraint tests in `tests/test_models.py`.

---

## Stage 3 Verification Summary

- [x] **Authentication Setup**:
  - Flask-Login initialized via `app/extensions.py` and connected via application factory.
  - User loader (`load_user`) implemented with safe integer casting and error handling.
  - `User` model integrates `UserMixin`, `is_active` status mapping, and Werkzeug password hashing helpers (`set_password`, `check_password`).
  - Authentication blueprint registered and wired with forms and routes.
- [x] **Registration**:
  - Responsive registration view (`/auth/register`) with name, email, password, and confirmation.
  - WTForms email normalization (strip and lowercase), length checks (minimum 8 characters), and duplicate email detection.
  - Client self-assignment of `admin` role strictly prevented on the server (hardcoded `student` role).
- [x] **Login and Logout**:
  - Responsive login view (`/auth/login`) with credential verification and session initialization (`login_user`, `logout_user`).
  - Suspended accounts blocked from logging in with a specific flash message.
  - Safe redirect helper (`is_safe_url`) to block open redirect attacks.
  - Generic authentication failure messages to prevent user enumeration.
- [x] **Authorization and User Pages**:
  - Reusable role-checking decorators (`@role_required`, `@admin_required`) enforcing server-side authorization.
  - Basic student dashboard (`/auth/dashboard` and `/dashboard`) displaying the logged-in user's name.
  - Profile page (`/auth/profile` and `/profile`) displaying user details strictly bound to `current_user` session, blocking URL parameter tampering.
  - Password hashes never exposed in views, templates, or responses.
- [x] **Security**:
  - CSRF protection enabled via Flask-WTF.
  - Passwords hashed using Werkzeug (`generate_password_hash`).

---

## Stage 4 Verification Summary

- [x] **Design System & Layout**:
  - Polished campus-themed design system in `app/static/css/style.css` using custom variables, accessible focus states (`:focus-visible`), and skip link navigation (`.skip-link`).
  - Enhanced `app/templates/base.html` with responsive navbar, guest vs. authenticated navigation states, categorical flash alert icons, and comprehensive campus assistance footer.
  - `app/static/js/main.js` supporting automatic alert dismissal, tooltip initialization, and form double-submit prevention.
- [x] **Homepage (`app/templates/index.html`)**:
  - Hero section explaining the campus recovery platform.
  - Search bar preview with category filter chips (clearly labeled as preview for Stage 6).
  - Prominent "Report Lost Item" and "Report Found Item" cards with visible "Coming Soon" badges.
  - 3-step "How It Works" workflow (Report $\rightarrow$ Claim & Verify $\rightarrow$ Reconnect).
  - Honest empty-state placeholders for Lost and Found item catalog feeds.
- [x] **Authentication Pages**:
  - Polished `app/templates/auth/login.html` and `app/templates/auth/register.html` with input groups, accessible labels, clear validation guidance, and CSRF token retention.
- [x] **Student Dashboard (`app/templates/auth/dashboard.html`)**:
  - Personalized greeting with the authenticated student's name (`Welcome, {{ user.name }}!`).
  - Honest zero-count overview widgets (no fabricated stats).
  - Clearly marked placeholders for future lost reports, found reports, claims, and notifications.
  - Direct navigation to student profile and homepage.
- [x] **Profile Page (`app/templates/auth/profile.html`)**:
  - Clean layout displaying Name, Email, Role, Account Status, and Member Since date.
  - Security reassurance noting cryptographic hash storage, with password hashes completely concealed.
- [x] **Testing**:
  - Added 11 UI tests in `tests/test_ui.py` validating guest/authenticated navigation states, search preview, report actions, accessibility skip links, form layouts, dashboard greeting, and profile components.

---

## Stage 5 Verification Summary

- [x] **Report Forms & Routes**:
  - Implemented authenticated routes `/items/report`, `/items/report/lost`, and `/items/report/found`.
  - Created WTForms `ItemReportForm` and `ItemEditForm` collecting title, description, category, color, location, incident date, and optional photograph.
  - Server-side validation enforcing required fields, length limits, future incident date rejection, and valid categories.
  - Enforced `current_user` association, automatic `item_type` setting (`lost` or `found`), and default status `open`.
  - Unauthenticated access strictly redirected to `/auth/login`.
- [x] **Secure Image Uploads**:
  - Enforced 5MB file-size limit (`MAX_CONTENT_LENGTH = 5 * 1024 * 1024`).
  - Strict format whitelisting (`JPG`, `PNG`, `WEBP`, `GIF`).
  - Binary header content inspection using Pillow (`Image.open`, `img.verify()`) to reject masqueraded malicious files.
  - Unguessable UUID-based server-side filenames (`uuid.uuid4().hex`) preventing directory traversal, collisions, and script execution.
  - Saved to `app/static/uploads/`, storing only relative filenames in SQLite.
  - Safe image cleanup helper (`delete_item_image`) ensuring deleted or replaced photographs are purged from disk.
- [x] **Browse Catalog & Pagination**:
  - Separate `/items/lost` and `/items/found` catalog views filtering items by `item_type`.
  - Ordered chronologically by incident date and creation timestamp.
  - Responsive card grids displaying title, category badge, color, location, incident date, thumbnail, and status badge.
  - Pagination controls via SQLAlchemy pagination (9 items per page).
  - Honest empty states when no listings exist, directing users to report items.
- [x] **Item Details & Privacy**:
  - Detail view `/items/<int:item_id>` displaying description, image, location, date, and status.
  - Safe reporter representation displaying only public name (`item.user.name`) — student email addresses and account credentials are strictly protected.
  - Non-existent item IDs handled with standard HTTP 404.
- [x] **User Report Management & Ownership Authorization**:
  - Personal dashboard `/items/my-items` allowing authenticated students to view only their own reports with status badges and quick actions.
  - Edit view `/items/<int:item_id>/edit` allowing report owners or administrators to update title, description, category, color, location, incident date, and status (`open`, `recovered`, `closed`).
  - Support for optional image removal or replacement with automatic disk file cleanup.
  - Strict server-side ownership authorization: non-owners receive HTTP 403 Forbidden.
  - Administrators authorized to moderate and edit any item listing.
- [x] **Frontend Integration**:
  - Replaced Stage 4 disabled placeholder buttons on homepage, navbar, and dashboard with active links to report and browse routes.
  - Responsive templates created: `report_choice.html`, `report.html`, `browse.html`, `detail.html`, `edit.html`, `my_items.html`.
- [x] **Testing**:
  - Created 23 comprehensive tests in `tests/test_items.py` covering auth protection, reporting workflows, validations, Pillow image verification, browse catalog, pagination, detail privacy, user report management, and 403 authorization.
  - Updated `tests/test_ui.py` to verify active report links.
  - Full test suite: **94 tests passing with 0 failures and 0 warnings**.

---

## Stage 7 Verification Summary

- [x] **Item Claiming Workflow (`app/claims/routes.py`, `app/claims/forms.py`)**:
  - `GET, POST /claims/item/<item_id>`: Authenticated students can submit ownership proof for found items with status `open`.
  - Prominent "Claim This Item" button displayed on found-item detail page for non-owner authenticated students.
  - Prevents non-authenticated users, owners claiming their own reports, claiming lost/closed/recovered items, and duplicate active claims (`pending` or `approved`).
  - WTForms server-side validation on proof description length (10-2000 characters).
  - CSRF protection enabled on all POST requests.
- [x] **Claim Review and Ownership Authorization (`app/claims/routes.py`)**:
  - Owner-exclusive "Pending Claims & Verification" section integrated into item details page (`/items/<item_id>`).
  - Strict authorization: non-owners receive HTTP 403 Forbidden; claimants are blocked from reviewing their own claim (HTTP 403).
  - Review actions `POST /claims/<claim_id>/approve` and `POST /claims/<claim_id>/reject` protected with CSRF.
  - Approval transaction sets claim status to `approved`, sets item status to `recovered`, sets `reviewer_id` and `reviewed_at`.
  - Blocks subsequent approval attempts on other pending claims for that item and prevents new claims.
  - Rejection transaction sets claim status to `rejected`, records reviewer and timestamp, leaves item open to receive other claims.
  - Prevents already approved or rejected claims from being reviewed again.
- [x] **User Claims Dashboard (`app/templates/claims/my_claims.html`)**:
  - `GET /claims/my-claims`: Displays current user's submitted claims with pagination, status badges (Pending, Approved, Rejected), timestamps, and item links.
  - Privacy preserved: claimants only view their own claims and proofs; unrelated users cannot view private verification details.
  - Added "My Claims" link to the authenticated navigation bar and student dashboard widget.
- [x] **Testing (`tests/test_claims.py`)**:
  - 15 comprehensive tests covering all 12 required scenarios, form validations, and CSRF protection.
  - Full test suite: **112 tests passing with 0 failures and 0 warnings**.

