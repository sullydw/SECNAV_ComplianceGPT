    # ── Joint signature blocks (senior on right, non-senior on left) ──
    # Signature blocks as left-aligned columns
    # Left: at left margin; Right: at standard signature position (page_width / 2)
    left_sig_x = left_margin
    right_sig_x = page.width / 2.0
    c.setFont("Times-Roman", 12)

    senior_sig = senior_cmd.get("signature", {})
    non_senior_sig = non_senior_cmd.get("signature", {})

    # Names on same row using drawString (not drawCentredString)
    c.drawString(left_sig_x, y, non_senior_sig.get("name", ""))
    c.drawString(right_sig_x, y, senior_sig.get("name", ""))
    y -= leading

    # Optional title/role lines - same x alignment as name
    senior_title = senior_sig.get("title_or_role", "")
    non_senior_title = non_senior_sig.get("title_or_role", "")
    if non_senior_title:
        c.drawString(left_sig_x, y, non_senior_title)
    if senior_title:
        c.drawString(right_sig_x, y, senior_title)

    # -- Copy to block (J3d) --
    y -= joint_letter_copy_gap  # additional space after signature title/role before Copy to
    copy_to_list = payload.get("copy_to")
    if copy_to_list:
        c.setFont("Times-Roman", 12)
        c.drawString(left_margin, y, "Copy to:")
        y -= leading
        for entry in copy_to_list:
            c.drawString(left_margin, y, entry)
            y -= leading
