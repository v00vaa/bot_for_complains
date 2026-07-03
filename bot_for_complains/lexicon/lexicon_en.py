LEXICON = {
    "forward": ">>",
    "backward": "<<",

    "/start_admin": (
        "Hello, administrator!"
    ),

    "/start_user": (
        "To report a bug press 'Report a bug' "
        "or 'Check bug status'. These buttons are also available in the bot menu."
    ),

    "add_admin": "Add administrator",

    "bug_list": "Bug list",

    "report_bt": "Report a bug",
    "status_bt": "Check bug status",

    "confirm": "Confirm",
    "not_confirm": "Do not confirm",

    "details": "Details",
    "new_bug": "New bug detected",
    "wrong_file_type": "Only .docx and .txt files are allowed.",
    "send_valid_file": "Please send a .docx or .txt file.",

    "no_bugs_user": "You have no registered bugs yet.",
    "no_bugs_admin": "There are no registered bugs yet.",

    "user_report": "User report",

    "remove_admin": "Remove administrator",

    "select_admin": "Select user",
    "select_admin_for_remove": "Select administrator",

    "admin_added": "Administrator successfully added.",
    "admin_removed": "Administrator successfully removed.",

    "already_admin": "This user is already an administrator.",
    "not_admin": "This user is not an administrator.",

    "choose_user_for_admin": (
        "Select a user to assign as administrator."
    ),
    "choose_admin_for_remove": (
        "Select an administrator to remove."
    ),

    "access_denied": (
        "This bug is assigned to another administrator."
    ),

    "status_waiting_confirmation": (
        "Waiting for user confirmation"
    ),

    "no_my_bugs": "You have no assigned bugs",

    # Version history
    "version_history": "Version history",
    "current_version": "Current version",

    # Bug list
    "select_bug": (
        "Select a report from the list "
        "or enter its number."
    ),

    "bugs_page": "Page",
    "no_history": "No change history available",

    # Admin bugs
    "my_bugs": "📌 My bugs",
    "all_bugs": "📋 All bugs",

    # Bug card buttons
    "accept": "Take into work",
    "complete_fix": "✅ Mark as fixed",
    "report_file": "📄 Download report",
    "invalid_description": "❌ Invalid report",

    # Statuses
    "status_new": "New",
    "status_in_progress": "In progress",
    "status_waiting_confirmation": "Waiting for confirmation",
    "status_reopened": "Reopened",
    "status_closed": "Closed",
    "status_invalid_description": "Invalid description",

    # Severity
    "severity_not_set": "Not set",
    "severity_critical": "Critical",
    "severity_high": "High",
    "severity_medium": "Medium",
    "severity_low": "Low",

    "severity_updated": "Severity updated",

    # Navigation
    "older_version": "◀ Older",
    "newer_version": "Newer ▶",

    # Card fields
    "bug_number": "ID",
    "version": "Version",
    "description": "Description",
    "severity": "Severity",
    "status": "Status",
    "user": "User",
    "report": "Report",

    "status_assigned_to": "Assignee",

    # User workflow
    "fix_completed_message": (
        "Fix completed.\n\n"
        "Please recheck the report and confirm "
        "that the issue has been resolved."
    ),
    "fix_completed": "User notified",
    "thank_you": "Thank you! The issue has been closed.",
    "invalid_description_message": (
        "Unfortunately, the report description was not detailed "
        "enough to fix the issue.\n\n"
        "Please describe the bug again in more detail:\n"
        "• what exactly you were doing;\n"
        "• which document you checked;\n"
        "• what you expected;\n"
        "• what actually happened.\n\n"
        "Then attach a new report."
    ),

    # Bug creation
    "cancel": "Cancel",
    "creation_cancelled": "Bug creation cancelled.",
    "enter_description": (
        "Describe the issue in as much detail as possible."
    ),
    "attach_report": (
        "Attach a report (.docx or .txt)."
    ),

    # Validation
    "bad_description": (
        "The description seems too short or not informative.\n\n"
        "Please include:\n"
        "• what actions were performed;\n"
        "• what was expected;\n"
        "• what actually happened."
    ),

    "marked_as_valid": (
        "Description marked as valid and will be used for model training."
    ),

    "marked_as_invalid": (
        "Description excluded from training dataset."
    ),

    # Training buttons
    "mark_valid": "✅ Use for training",
    "mark_invalid": "❌ Do not use for training",

    # Admin messages
    "bug_accepted": "Bug accepted for processing",
    "bug_registered": "Your report has been registered.",
    "bug_not_found": "Report not found",

    # General
    "history_empty": "No change history available.",
    "current": "Current",
}