package com.complaintops.backend;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.time.LocalDateTime;

@Entity
@Table(name = "complaints")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Complaint {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // originalText KALDIRILDI - KVKK / Data Minimization
    // Ham metin artık DB'de saklanmıyor

    @Column(columnDefinition = "TEXT")
    private String maskedText;

    private String category;
    private String urgency;

    @Column(columnDefinition = "TEXT")
    private String actionPlan; // Stored as JSON string or simple text

    @Column(columnDefinition = "TEXT")
    private String customerReplyDraft;

    @Column(columnDefinition = "TEXT")
    private String sources; // JSON array of RAG source references for explainability

    // Human-in-the-Loop fields
    private Boolean needsHumanReview = false;
    private String reviewId;

    // Confidence scores for explainability
    private Double categoryConfidence;
    private Double urgencyConfidence;

    // Graceful degradation status flags
    private String ragStatus = "OK"; // OK, UNAVAILABLE, ERROR
    private String llmStatus = "OK"; // OK, TEMPLATE_FALLBACK, ERROR

    @Enumerated(EnumType.STRING)
    private ComplaintStatus status = ComplaintStatus.NEW;

    private LocalDateTime createdAt = LocalDateTime.now();
}

enum ComplaintStatus {
    NEW,
    MASKING_FAILED, // PII maskeleme hatası - manuel inceleme gerekli
    ANALYZED,
    RESOLVED
}
