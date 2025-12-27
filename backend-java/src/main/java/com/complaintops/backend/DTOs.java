package com.complaintops.backend;

import lombok.Data;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class DTOs {

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class MaskingRequest {
        private String text;
    }

    @Data
    public static class MaskingResponse {
        @JsonProperty("original_text")
        private String originalText;

        @JsonProperty("masked_text")
        private String maskedText;

        @JsonProperty("masked_entities")
        private List<String> maskedEntities;
    }

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class TriageRequest {
        private String text;
    }

    @Data
    public static class TriageResponse {
        private String category;

        @JsonProperty("category_confidence")
        private double categoryConfidence;

        private String urgency;

        @JsonProperty("urgency_confidence")
        private double urgencyConfidence;
    }

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class RAGRequest {
        private String text;
    }

    @Data
    public static class RAGResponse {
        @JsonProperty("relevant_snippets")
        private List<String> relevantSnippets;
    }

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class GenerateRequest {
        private String text;
        private String category;
        private String urgency;

        @JsonProperty("relevant_snippets")
        private List<String> relevantSnippets;
    }

    @Data
    public static class GenerateResponse {
        @JsonProperty("action_plan")
        private List<String> actionPlan;

        @JsonProperty("customer_reply_draft")
        private String customerReplyDraft;

        @JsonProperty("risk_flags")
        private List<String> riskFlags;

        @JsonProperty("sources")
        private List<SourceItem> sources;
    }

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class SourceItem {
        @JsonProperty("doc_name")
        private String docName;

        private String source;
        private String snippet;

        @JsonProperty("chunk_id")
        private String chunkId;
    }

    @Data
    public static class TriageResponseFull {
        private String category;

        @JsonProperty("category_confidence")
        private double categoryConfidence;

        private String urgency;

        @JsonProperty("urgency_confidence")
        private double urgencyConfidence;

        @JsonProperty("needs_human_review")
        private boolean needsHumanReview;

        @JsonProperty("review_id")
        private String reviewId;

        @JsonProperty("review_status")
        private String reviewStatus;
    }
}
