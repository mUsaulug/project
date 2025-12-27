package com.complaintops.backend;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.time.LocalDateTime;

/**
 * Entity for tracking complaint edits (audit trail).
 * Based on ADR-004: Audit Trail for Response Editing
 */
@Entity
@Table(name = "complaint_edits")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ComplaintEdit {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "complaint_id", nullable = false)
    private Long complaintId;

    @Column(name = "field_name", nullable = false, length = 50)
    private String fieldName; // 'customer_reply_draft', 'action_plan', etc.

    @Column(columnDefinition = "TEXT")
    private String oldValue;

    @Column(columnDefinition = "TEXT")
    private String newValue;

    @Column(name = "edited_by", length = 100)
    private String editedBy;

    @Column(name = "edited_at")
    private LocalDateTime editedAt = LocalDateTime.now();

    @Column(name = "edit_reason", length = 255)
    private String editReason;
}
